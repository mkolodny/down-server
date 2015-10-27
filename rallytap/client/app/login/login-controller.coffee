class LoginCtrl
  @$inject: ['$meteor', '$state', '$stateParams', '$window', 'Auth',
             'Invitation', 'LinkInvitation', 'localStorageService', 'User']
  constructor: (@$meteor, @$state, @$stateParams, @$window, @Auth,
                @Invitation, @LinkInvitation, localStorageService, @User) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser
    @localStorage = localStorageService

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
    @$meteor.loginWithPassword "#{user.id}", user.authtoken
      .then =>
        # Persist the user to local storage.
        @Auth.user = new @User user
        @localStorage.set 'currentUser', @Auth.user
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
