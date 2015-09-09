class LoginCtrl
  constructor: (@$state, @$stateParams, @$window, @Auth, @Asteroid,
                @Invitation, @LinkInvitation) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser

    # Load the Facebook javascript SDK.
    id = 'facebook-jssdk'
    if not document.getElementById id
      js = document.createElement 'script'
      js.id = id
      js.async = true
      js.src = "//connect.facebook.net/en_US/sdk.js"
      ref = document.getElementsByTagName('script')[0]
      ref.parentNode.insertBefore js, ref

    # Init Facebook SDK
    @$window.fbAppId = '864552050271610' # TODO: Set this via DJANGO!
    @$window.fbAsyncInit = =>
      FB.init
        appId: @$window.fbAppId
        xfbml: true
        version: 'v2.3'

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
      .then (linkInvitation) =>
        memberResponses = [@Invitation.accepted, @Invitation.maybe]
        if linkInvitation.invitation.response in memberResponses
          @$state.go 'event', linkInvitation
        else
          @$state.go 'invitation', linkInvitation
      , =>
        @fetchInvitationError = true

module.exports = LoginCtrl
