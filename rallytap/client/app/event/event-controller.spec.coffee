require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/meteor/meteor-mocks'
require 'down-ionic/app/common/auth/auth-module'
EventCtrl = require './event-controller'

fdescribe 'event controller', ->
  $controller = null
  $meteor = null
  $state = null
  $q = null
  $rootScope = null
  $window = null
  Auth = null
  chatsCollection = null
  ctrl = null
  data = null
  deferredGetMemberInvitations = null
  deferredSubscribe = null
  Event = null
  event = null
  fromUser = null
  Invitation = null
  invitation = null
  linkId = null
  Messages = null
  messages = null
  messagesCollection = null
  messagesRQ = null
  scope = null
  User = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('angular-meteor')

  beforeEach angular.mock.module('rallytap.auth')

  beforeEach angular.mock.module('rallytap.resources')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $meteor = $injector.get '$meteor'
    $state = $injector.get '$state'
    $q = $injector.get '$q'
    $window = $injector.get '$window'
    Auth = $injector.get 'Auth'
    Event = $injector.get 'Event'
    Invitation = $injector.get 'Invitation'
    scope = $injector.get '$rootScope'
    User = $injector.get 'User'

    Auth.user =
      id: 1
      name: 'Jimbo Walker'

    event =
      id: 123
    fromUser =
      id: 456
    invitation =
      id: 789
    linkId = '123'
    data =
      event: event
      fromUser: fromUser
      invitation: invitation
      linkId: linkId

    # Create mocks/spies for getting the messages for this event.
    messagesCollection = 'messagesCollection'
    chatsCollection = 'chatsCollection'
    $meteor.getCollectionByName.and.callFake (collectionName) ->
      if collectionName is 'messages' then return messagesCollection
      if collectionName is 'chats' then return chatsCollection

    deferredSubscribe = $q.defer()
    scope.$meteorSubscribe = jasmine.createSpy '$scope.$meteorSubscribe'
      .and.returnValue deferredSubscribe.promise

    ctrl = $controller EventCtrl,
      Auth: Auth
      data: data
      $scope: scope
  )

  it 'should set the current user on the controller', ->
    expect(ctrl.currentUser).toBe Auth.user

  it 'should set the event on the controller', ->
    expect(ctrl.event).toBe event

  it 'should set the from user on the controller', ->
    expect(ctrl.fromUser).toBe fromUser

  it 'should set the invitation on the controller', ->
    expect(ctrl.invitation).toBe invitation

  it 'should set the linkId on the controller', ->
    expect(ctrl.linkId).toBe linkId

  it 'should set the messages collection on the controller', ->
    expect($meteor.getCollectionByName).toHaveBeenCalledWith 'messages'
    expect(ctrl.Messages).toBe messagesCollection

  it 'should set the events collection on the controller', ->
    expect($meteor.getCollectionByName).toHaveBeenCalledWith 'chats'
    expect(ctrl.Chats).toBe chatsCollection

  it 'should subscribe to the events messages', ->
    expect(scope.$meteorSubscribe).toHaveBeenCalledWith 'chat', "#{event.id}"

  describe 'when the view begins loading', ->
    message = null
    messages = null
    chat = null

    beforeEach ->
      spyOn ctrl, 'updateMembers'
      spyOn ctrl, 'getMessages'
      spyOn ctrl, 'handleNewMessage'

      message =
        _id: 1
        creator: new User Auth.user
        createdAt:
          $date: new Date().getTime()
        text: 'I\'m in love with a robot.'
        chatId: "#{event.id}"
        type: 'text'
      messages = [message]
      $meteor.collection.and.returnValue messages

      chat =
        members: []
      spyOn(ctrl, 'getChat').and.returnValue chat

      spyOn ctrl, 'handleChatMembersChange'
      spyOn ctrl, 'watchNewestMessage'

      scope.$emit '$viewContentLoading'
      scope.$apply()

    it 'should watch the newestMessage', ->
      expect(ctrl.watchNewestMessage).toHaveBeenCalled()

    it 'should bind the messages to the controller', ->
      # TODO: Check that controller property is set
      expect($meteor.collection).toHaveBeenCalledWith ctrl.getMessages, false

    it 'should bind the meteor event members to the controller', ->
      expect(ctrl.chat).toEqual chat
      expect(ctrl.getChat).toHaveBeenCalled()

    it 'should update the members array', ->
      expect(ctrl.updateMembers).toHaveBeenCalled()

    describe 'when the chat changes', ->
      chatMembers = null

      beforeEach ->
        chatMembers = [
          userId: '1'
        ,
          userId: '2'
        ]
        ctrl.chat.members = chatMembers

        ctrl.handleChatMembersChange.calls.reset()
        scope.$apply()

      it 'should handle the change', ->
        expect(ctrl.handleChatMembersChange).toHaveBeenCalled()


  ##watchNewestMessage
  describe 'watching new messages coming in', ->

    describe 'when new messages get posted', ->

      beforeEach ->
        spyOn ctrl, 'handleNewMessage'

        message =
          _id: 'asdfs'
          creator: new User Auth.user
          createdAt: new Date()
          text: 'I\'m in love with a robot.'
          type: 'text'

        ctrl.watchNewestMessage()

        # Trigger watch
        ctrl.messages = [message]
        scope.$apply()

      it 'should handle the new message', ->
        expect(ctrl.handleNewMessage).toHaveBeenCalled()


  describe 'handling a new message', ->
    newMessageId = null

    beforeEach ->
      newMessageId = '1jkhkgfjgfhftxhgdxf'

      ctrl.handleNewMessage newMessageId

    it 'should mark the message as read', ->
      expect($meteor.call).toHaveBeenCalledWith 'readMessage', newMessageId


  describe 'getting messages', ->
    cursor = null
    result = null

    beforeEach ->
      cursor = 'messagesCursor'
      ctrl.Messages =
        find: jasmine.createSpy('Messages.find').and.returnValue cursor
      result = ctrl.getMessages()

    it 'should return a messages reactive cursor', ->
      expect(result).toBe cursor

    it 'should query, sort and transform messages', ->
      selector =
        chatId: "#{ctrl.event.id}"
      options =
        sort:
          createdAt: 1
        transform: ctrl.transformMessage
      expect(ctrl.Messages.find).toHaveBeenCalledWith selector, options


  describe 'getting the newest message', ->
    result = null
    newestMessage = null

    beforeEach ->
      newestMessage = 'newestMessage'
      $meteor.object.and.returnValue newestMessage
      result = ctrl.getNewestMessage()

    it 'should return a AngularMeteorObject', ->
      expect(result).toEqual newestMessage

    it 'should filter object by event id and sort by created at', ->
      selector =
        chatId: "#{ctrl.event.id}"
      options =
        sort:
          createdAt: -1
      expect($meteor.object).toHaveBeenCalledWith(ctrl.Messages, selector, false,
          options)


  describe 'getting meteor chat', ->
    result = null
    chat = null

    beforeEach ->
      chat = 'chat'
      $meteor.object.and.returnValue chat
      result = ctrl.getChat()

    it 'should return an AngularMeteorObject', ->
      expect(result).toEqual chat

    it 'should filter for the current event', ->
      selector =
        chatId: "#{ctrl.event.id}"
      expect($meteor.object).toHaveBeenCalledWith ctrl.Chats, selector, false


  describe 'transforming messages', ->
    message = null
    result = null

    beforeEach ->
      message =
        creator: {}
      result = ctrl.transformMessage message

    it 'should create a new User object with the message.creator', ->
      expectedResult = angular.copy message
      expectedResult.creator = new User expectedResult.creator

      expect(result).toEqual expectedResult


  describe 'handling chat members changes', ->

    describe 'when users are added or removed', ->
      member1 = null
      member2 = null

      beforeEach ->
        member1 =
          id: 1
          name: 'Jim Bob'
        member2 =
          id: 2
          name: 'The Other Guy'
        ctrl.members = [member1, member2]

        spyOn ctrl, 'updateMembers'
        ctrl.handleChatMembersChange [{userId: 1}]

      it 'should update members', ->
        expect(ctrl.updateMembers).toHaveBeenCalled()


  describe 'updating the members array', ->
    deferred = null

    beforeEach ->
      deferred = $q.defer()
      spyOn(Invitation, 'getMemberInvitations').and.returnValue
        $promise: deferred.promise

      ctrl.updateMembers()

    describe 'successfully', ->
      acceptedInvitation = null
      maybeInvitation = null
      invitations = null

      beforeEach ->
        acceptedInvitation = angular.extend {}, invitation,
          response: Invitation.accepted
        maybeInvitation = angular.extend {}, invitation,
          response: Invitation.maybe
        invitations = [acceptedInvitation, maybeInvitation]
        deferred.resolve invitations
        scope.$apply()

      it 'should set the accepted/maybe invitations on the controller', ->
        memberInvitations = [acceptedInvitation, maybeInvitation]
        members = (invitation.toUser for invitation in memberInvitations)
        expect(ctrl.members).toEqual members


    describe 'unsuccessfully', ->

      beforeEach ->
        deferred.reject()
        scope.$apply()

      it 'should show an error', ->
        # TODO: Show the error in the view.
        expect(ctrl.membersError).toBe true


  describe 'sending a download link', ->
    downloadPhone = null

    beforeEach ->
      scope.sendSMSForm =
        $valid: true
      $window.branch =
        sendSMS: jasmine.createSpy 'branch.sendSMS'
      downloadPhone = '+19252852230'
      ctrl.downloadPhone = downloadPhone

      ctrl.sendSMS()

    it 'should send the sms', ->
      linkData =
        channel: 'WebView'
        feature: 'Text-To-Download'
      expect($window.branch.sendSMS).toHaveBeenCalledWith downloadPhone, linkData

    it 'should clear the form', ->
      expect(ctrl.downloadPhone).toBeNull()


  describe 'when there is a redirect view', ->
    redirectView = null

    beforeEach ->
      redirectView = 'login'
      data.redirectView = redirectView

      spyOn $state, 'go'

      ctrl = $controller EventCtrl,
        Auth: Auth
        data: data
        $scope: scope

    it 'should go to the redirect state', ->
      expect($state.go).toHaveBeenCalledWith redirectView,
        event: event
        fromUser: fromUser
        invitation: invitation
        linkId: linkId


  describe 'when there is an error', ->

    beforeEach ->
      data =
        error: true

      ctrl = $controller EventCtrl,
        Auth: Auth
        data: data
        $scope: scope

    it 'should return without doing anything', ->


  describe 'checking whether a message is an action message', ->
    message = null

    beforeEach ->
      message =
        _id: 1
        creator:
          id: 2
          name: 'Guido van Rossum'
          imageUrl: 'http://facebook.com/profile-pics/vrawesome'
        createdAt:
          $date: new Date().getTime()
        text: 'I\'m in love with a robot.'
        eventId: event.id

    describe 'when it is an accept action', ->

      beforeEach ->
        message.type = Invitation.acceptAction

      it 'should return true', ->
        expect(ctrl.isActionMessage message).toBe true


    describe 'when it is an maybe action', ->

      beforeEach ->
        message.type = Invitation.maybeAction

      it 'should return true', ->
        expect(ctrl.isActionMessage message).toBe true


    describe 'when it is a decline action', ->

      beforeEach ->
        message.type = Invitation.declineAction

      it 'should return true', ->
        expect(ctrl.isActionMessage message).toBe true


    describe 'when it\'s text', ->

      beforeEach ->
        message.type = 'text'

      it 'should return false', ->
        expect(ctrl.isActionMessage message).toBe false


  describe 'checking whether a message is the current user\'s message', ->
    message = null

    beforeEach ->
      message =
        _id: 1
        creator:
          id: 2
          name: 'Guido van Rossum'
          imageUrl: 'http://facebook.com/profile-pics/vrawesome'
        createdAt:
          $date: new Date().getTime()
        text: 'I\'m in love with a robot.'
        eventId: event.id
      Auth.user =
        id: 1
        name: 'Alan Turing'
        username: 'tdog'
        imageUrl: 'https://facebook.com/profile-pics/tdog'
        location:
          lat: 40.7265834
          long: -73.9821535

    describe 'when it is', ->

      beforeEach ->
        message.creator.id = "#{Auth.user.id}" # Meteor likes strings

      it 'should return true', ->
        expect(ctrl.isMyMessage message).toBe true


    describe 'when it isn\'t', ->

      beforeEach ->
        message.creator.id = "#{Auth.user.id + 1}" # Meteor likes strings

      it 'should return false', ->
        expect(ctrl.isMyMessage message).toBe false


  describe 'sending a message', ->
    message = null

    beforeEach ->
      message = 'this is gonna be dope!'
      ctrl.message = message
      spyOn Event, 'sendMessage'

      ctrl.sendMessage()

    it 'should send the message', ->
      expect(Event.sendMessage).toHaveBeenCalledWith event, message

    it 'should clear the message', ->
      expect(ctrl.message).toBeNull()


  # Copied from invitation-controller.spec.coffee
  describe 'checking whether the user accepted their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.accepted

      it 'should return true', ->
        expect(ctrl.wasAccepted()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.maybe

      it 'should return false', ->
        expect(ctrl.wasAccepted()).toBe false


  describe 'checking whether the user responded maybe their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.maybe

      it 'should return true', ->
        expect(ctrl.wasMaybed()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.accepted

      it 'should return false', ->
        expect(ctrl.wasMaybed()).toBe false


  describe 'checking whether the user declined their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.declined

      it 'should return true', ->
        expect(ctrl.wasDeclined()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        ctrl.invitation.response = Invitation.maybe

      it 'should return false', ->
        expect(ctrl.wasDeclined()).toBe false



  describe 'responding to the invitation', ->
    response = null
    deferred = null

    beforeEach ->
      # Mock the current invitation response.
      response = Invitation.declined
      ctrl.invitation.response = response

      deferred = $q.defer()
      spyOn(Invitation, 'updateResponse').and.returnValue
        $promise: deferred.promise
      spyOn $state, 'go'

      ctrl.respondToInvitation response

    it 'should update the invitation', ->
      expect(Invitation.updateResponse).toHaveBeenCalledWith invitation, response

    describe 'successfully', ->

      beforeEach ->
        deferred.resolve invitation
        scope.$apply()

      it 'should set the invitation on the controller', ->
        expect(ctrl.invitation).toEqual invitation

      describe 'when the response is declined', ->

        it 'should go to the invitation view', ->
          expect($state.go).toHaveBeenCalledWith 'invitation',
            event: event
            fromUser: fromUser
            invitation: invitation
            linkId: linkId


    describe 'unsuccessfully', ->

      beforeEach ->
        deferred.reject()
        scope.$apply()

      xit 'show an error', ->
        error = 'For some reason, that didn\'t work.'
        expect(ctrl.error).toBe error


  describe 'accepting the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.acceptInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.accepted


  describe 'responding maybe to the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.maybeInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.maybe


  describe 'declining the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.declineInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.declined
