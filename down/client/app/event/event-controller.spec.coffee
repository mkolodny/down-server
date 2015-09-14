require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/asteroid/asteroid-module'
EventCtrl = require './event-controller'

describe 'event controller', ->
  $controller = null
  $state = null
  $q = null
  $rootScope = null
  Auth = null
  Asteroid = null
  Event = null
  Invitation = null
  ctrl = null
  data = null
  deferredGetMemberInvitations = null
  event = null
  fromUser = null
  invitation = null
  linkId = null
  Messages = null
  messages = null
  messagesRQ = null
  scope = null
  User = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.asteroid')

  beforeEach angular.mock.module('down.resources')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $state = $injector.get '$state'
    $q = $injector.get '$q'
    Auth = angular.copy $injector.get('Auth')
    Asteroid = $injector.get 'Asteroid'
    Event = $injector.get 'Event'
    Invitation = $injector.get 'Invitation'
    scope = $injector.get '$rootScope'
    User = $injector.get 'User'

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
    spyOn Asteroid, 'subscribe'
    messagesRQ =
      on: jasmine.createSpy 'messagesRQ.on'
      result: []
    Messages =
      reactiveQuery: jasmine.createSpy('Messages.reactiveQuery') \
          .and.returnValue messagesRQ
    spyOn(Asteroid, 'getCollection').and.returnValue Messages

    deferredGetMemberInvitations = $q.defer()
    spyOn(Invitation, 'getMemberInvitations').and.returnValue
      $promise: deferredGetMemberInvitations.promise

    ctrl = $controller EventCtrl,
      Auth: Auth
      data: data
  )

  it 'should set the event on the controller', ->
    expect(ctrl.event).toBe event

  it 'should set the from user on the controller', ->
    expect(ctrl.fromUser).toBe fromUser

  it 'should set the invitation on the controller', ->
    expect(ctrl.invitation).toBe invitation

  it 'should request the event members\' invitations', ->
    expect(Invitation.getMemberInvitations).toHaveBeenCalledWith {id: event.id}

  it 'should subscribe to the events messages', ->
    expect(Asteroid.subscribe).toHaveBeenCalledWith 'event', event.id

  it 'should get the messages collection', ->
    expect(Asteroid.getCollection).toHaveBeenCalledWith 'messages'

  it 'should set the messages collection on the controller', ->
    expect(ctrl.Messages).toBe Messages

  it 'should ask for the messages for the event', ->
    expect(Messages.reactiveQuery).toHaveBeenCalledWith {eventId: "#{event.id}"}

  it 'should set the messages reactive query on the controller', ->
    expect(ctrl.messagesRQ).toBe messagesRQ

  it 'should listen for new messages', ->
    expect(messagesRQ.on).toHaveBeenCalledWith 'change', ctrl.showMessages

  describe 'when there is a redirect view', ->
    redirectView = null

    beforeEach ->
      redirectView = 'login'
      data.redirectView = redirectView

      spyOn $state, 'go'

      ctrl = $controller EventCtrl,
        Auth: Auth
        data: data

    it 'should go to the redirect state', ->
      expect($state.go).toHaveBeenCalledWith redirectView,
        event: event
        fromUser: fromUser
        invitation: invitation
        linkId: linkId


  xdescribe 'when there is an error', ->

    beforeEach ->
      data.error = true


  describe 'when the invitations return successfully', ->
    acceptedInvitation = null
    maybeInvitation = null
    invitations = null

    beforeEach ->
      acceptedInvitation = angular.extend {}, invitation,
        response: Invitation.accepted
      maybeInvitation = angular.extend {}, invitation,
        response: Invitation.maybe
      invitations = [acceptedInvitation, maybeInvitation]
      deferredGetMemberInvitations.resolve invitations
      scope.$apply()

    it 'should set the accepted/maybe invitations on the controller', ->
      memberInvitations = [acceptedInvitation, maybeInvitation]
      members = (invitation.toUser for invitation in memberInvitations)
      expect(ctrl.members).toEqual members


  describe 'when the invitations return unsuccessfully', ->

    beforeEach ->
      deferredGetMemberInvitations.reject()
      scope.$apply()

    it 'should show an error', ->
      # TODO: Show the error in the view.
      expect(ctrl.membersError).toBe true


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


  describe 'handling when messages change', ->
    earlierMessage = null
    laterMessage = null

    beforeEach ->
      # Mock the current date.
      jasmine.clock().install()
      currentDate = new Date 1438195002656
      jasmine.clock().mockDate currentDate

      earlier = new Date()
      later = new Date earlier.getTime()+1000
      creator =
        id: 2
        name: 'Guido van Rossum'
        imageUrl: 'http://facebook.com/profile-pics/vrawesome'
      earlierMessage =
        _id: 1
        creator: creator
        createdAt:
          $date: earlier
        text: 'I\'m in love with a robot.'
        eventId: event.id
        type: 'text'
      laterMessage =
        _id: 1
        creator: creator
        createdAt:
          $date: later
        text: 'Michael Jordan is down'
        eventId: event.id
        type: 'action'
      messages = [laterMessage, earlierMessage]

      messagesRQ =
        result: messages
      ctrl.messagesRQ = messagesRQ

      spyOn Asteroid, 'call'

      ctrl.showMessages()

    afterEach ->
      jasmine.clock().uninstall()

    it 'should set the messages on the event from oldest to newest', ->
      laterMessage.creator = new User laterMessage.creator
      earlierMessage.creator = new User earlierMessage.creator
      expect(ctrl.messages).toEqual [earlierMessage, laterMessage]

    it 'should mark the newest message as read', ->
      expect(Asteroid.call).toHaveBeenCalledWith 'readMessage', laterMessage._id


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
      ctrl.linkId = linkId

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
