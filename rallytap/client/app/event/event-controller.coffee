class EventCtrl
  @$inject: ['$meteor', '$rootScope', '$scope', '$state', '$stateParams',
             '$window', 'Auth', 'data', 'Event', 'Invitation', 'User']
  constructor: (@$meteor, @$rootScope, @$scope, @$state, @$stateParams, @$window,
                @Auth, @data, @Event, @Invitation, @User) ->
    if @data.redirectView
      @$state.go @data.redirectView,
        event: @data.event
        fromUser: @data.fromUser
        invitation: @data.invitation
        linkId: @data.linkId
      return

    if @data.error
      return

    @currentUser = @Auth.user
    @event = @data.event
    @fromUser = @data.fromUser
    @invitation = @data.invitation
    @linkId = @data.linkId

    # Set Meteor collections on controller
    @Messages = @$meteor.getCollectionByName 'messages'
    @Chats = @$meteor.getCollectionByName 'chats'

    # Subscribe to the event's chat.
    @$scope.$meteorSubscribe 'chat', "#{@event.id}"

    @$rootScope.$on '$viewContentLoaded', =>
      # Get the members invitations.
      @updateMembers()

      # Bind reactive variables
      @messages = @$meteor.collection @getMessages, false
      @newestMessage = @getNewestMessage()
      @chat = @getChat()

      # Watch for changes in newest message
      @watchNewestMessage()

      # Watch for changes in chat members
      @$scope.$watch =>
        @chat.members
      , @handleChatMembersChange

  watchNewestMessage: =>
    # Mark messages as read as they come in
    #   and scroll to bottom
    @$scope.$watch =>
      newestMessage = @messages[@messages.length-1]
      if angular.isDefined newestMessage
        newestMessage._id
    , @handleNewMessage

  handleNewMessage: (newMessageId) =>
    if newMessageId is undefined
      return

    @$meteor.call 'readMessage', newMessageId

  getMessages: =>
    @Messages.find
      chatId: "#{@event.id}"
    ,
      sort:
        createdAt: 1
      transform: @transformMessage

  transformMessage: (message) =>
    message.creator = new @User message.creator
    message

  getNewestMessage: =>
    selector =
      chatId: "#{@event.id}"
    options =
      sort:
        createdAt: -1
    @$meteor.object @Messages, selector, false, options

  getChat: =>
    selector =
      chatId: "#{@event.id}"
    @$meteor.object @Chats, selector, false

  handleChatMembersChange: (chatMembers) =>
    chatMembers = chatMembers or []
    members = @members or []

    chatMemberIds = (member.userId for member in chatMembers)
    currentMemberIds = (member.id for member in members)
    chatMemberIds.sort()
    currentMemberIds.sort()

    if not angular.equals chatMemberIds, currentMemberIds
      @updateMembers()

  updateMembers: =>
    @Invitation.getMemberInvitations {id: @event.id}
      .$promise.then (invitations) =>
        @members = (invitation.toUser for invitation in invitations)
        if not @$scope.$$phase
          @$scope.$digest()
      , =>
        @membersError = true

  sendSMS: ->
    if not @$scope.sendSMSForm.$valid then return

    linkData =
      channel: 'WebView'
      feature: 'Text-To-Download'
    @$window.branch.sendSMS @downloadPhone, linkData
    @downloadPhone = null

  showMessages: =>
    @messages = angular.copy @messagesRQ.result
    for message in @messages
      message.creator = new @User message.creator

    # Sort the messages from oldest to newest.
    @messages.sort (a, b) ->
      if a.createdAt.$date < b.createdAt.$date
        return -1
      else
        return 1

    # Mark newest message as read
    if @messages.length > 0
      newestMessage = @messages[@messages.length - 1]
      @Asteroid.call 'readMessage', newestMessage._id

    # Call digest
    if not @$scope.$$phase
      @$scope.$digest()

  isActionMessage: (message) ->
    actions = [
      @Invitation.acceptAction
      @Invitation.maybeAction
      @Invitation.declineAction
    ]
    message.type in actions

  isMyMessage: (message) ->
    message.creator.id is "#{@Auth.user.id}" # Meteor likes strings

  sendMessage: ->
    @Event.sendMessage @event, @message
    @message = null

  wasAccepted: ->
    @invitation?.response is @Invitation.accepted

  wasMaybed: ->
    @invitation?.response is @Invitation.maybe

  wasDeclined: ->
    @invitation?.response is @Invitation.declined

  acceptInvitation: ->
    @respondToInvitation @Invitation.accepted

  maybeInvitation: ->
    @respondToInvitation @Invitation.maybe

  declineInvitation: ->
    @respondToInvitation @Invitation.declined

  respondToInvitation: (response) ->
    @Invitation.updateResponse @invitation, response
      .$promise.then (invitation) =>
        @invitation = invitation
        if invitation.response is @Invitation.declined
          @$state.go 'invitation',
            event: @event
            fromUser: @fromUser
            invitation: @invitation
            linkId: @linkId
      , =>
        @error = 'For some reason, that didn\'t work.'

module.exports = EventCtrl
