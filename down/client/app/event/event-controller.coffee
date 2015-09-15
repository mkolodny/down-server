class EventCtrl
  @$inject: ['$state', '$stateParams', 'Asteroid', 'Auth', 'Event',
             'Invitation', 'User', 'data']
  constructor: (@$state, @$stateParams, @Asteroid, @Auth, @Event,
                @Invitation, @User, @data) ->
    if @data.redirectView
      @$state.go @data.redirectView,
        event: @data.event
        fromUser: @data.fromUser
        invitation: @data.invitation
        linkId: @data.linkId
      return

    @currentUser = @Auth.user
    @event = @data.event
    @fromUser = @data.fromUser
    @invitation = @data.invitation
    @linkId = @data.linkId

    # Get/subscribe to the messages posted in this event.
    @Asteroid.subscribe 'event', @event.id
    @Messages = @Asteroid.getCollection 'messages'
    @messagesRQ = @Messages.reactiveQuery {eventId: "#{@event.id}"}
    @showMessages()

    # Watch for new messages.
    @messagesRQ.on 'change', @showMessages

    @Invitation.getMemberInvitations {id: @event.id}
      .$promise.then (invitations) =>
        @members = (invitation.toUser for invitation in invitations)
      , =>
        @membersError = true

    # Add branch web sdk
    ((b, r, a, n, c, h, _, s, d, k) ->
      if !b[n] or !b[n]._q
        while s < _.length
          c h, _[s++]
        d = r.createElement(a)
        d.async = 1
        d.src = 'https://cdn.branch.io/branch-v1.6.10.min.js'
        k = r.getElementsByTagName(a)[0]
        k.parentNode.insertBefore d, k
        b[n] = h
      return
    ) window, document, 'script', 'branch', ((b, r) ->

      b[r] = ->
        b._q.push [
          r
          arguments
        ]
        return

      return
    ), {
      _q: []
      _v: 1
    }, 'init data first addListener removeListener setIdentity logout track link sendSMS referrals credits creditHistory applyCode validateCode getCode redeem banner closeBanner'.split(' '), 0

    @initBranch()

  # used for text to download links
  initBranch: ->
    # TODO : SET THIS FROM DJANGO!!
    @$window.branchApiKey = 'key_test_ogfq42bC7tuGVWdMjNm3sjflvDdOBJiv'
    @$window.branch.init @$window.branchApiKey

  sendSMS: ->
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
