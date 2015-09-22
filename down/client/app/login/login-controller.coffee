class LoginCtrl
  @$inject: ['$state', '$stateParams', '$window', 'Auth', 'Asteroid',
             'Invitation', 'LinkInvitation']
  constructor: (@$state, @$stateParams, @$window, @Auth, @Asteroid,
                @Invitation, @LinkInvitation) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser

  login: ->
    @$window.FB.login @handleFBLogin

  handleFBLogin: (response) =>
    if response.authResponse
      @Auth.facebookLogin response.authResponse.accessToken
        .then (user) =>
          @meteorLogin user
        , =>
          @loginFailed = true
    else
      @fbLoginCanceled = true

  meteorLogin: (user) ->
    @Asteroid.login().then =>
      # Persist the user to local storage.
      @Auth.setUser user
      @getLinkData()
    , =>
      @error = 'Oops, something went wrong.'

  getLinkData: ->
    @LinkInvitation.getByLinkId {linkId: @$stateParams.linkId}
      .$promise.then (linkInvitation) =>
        memberResponses = [@Invitation.accepted, @Invitation.maybe]
        if linkInvitation.invitation.response in memberResponses
          @$state.go 'event', linkInvitation
        else
          @$state.go 'invitation', linkInvitation
      , =>
        @fetchInvitationError = true

module.exports = LoginCtrl
