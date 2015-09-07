class LoginCtrl
  constructor: (@$state, @$stateParams, @$window, @Auth, @Asteroid,
                @EventService) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser

    # Add Facebook SDK
    ((d, s, id) ->
      js = undefined
      fjs = d.getElementsByTagName(s)[0]
      if d.getElementById(id)
        return
      js = d.createElement(s)
      js.id = id
      js.src = '//connect.facebook.net/en_US/sdk.js'
      fjs.parentNode.insertBefore js, fjs
      return
    ) document, 'script', 'facebook-jssdk'

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
    accessToken = response.authResponse?.accessToken
    if accessToken
      @Auth.authWithFacebook(accessToken)
        .then (user) =>
          @meteorLogin user

  meteorLogin: (user) ->
    console.log user
    @Asteroid.login().then =>
      console.log "SUCCESS"
      # Persist the user to local storage.
      @Auth.setUser user
      @getLinkData()
    , =>
      console.log "SOMETHING WRONG"
      @error = 'Oops, something went wrong.'

  getLinkData: ->
    @EventService.getData()
      .then (data) =>
        nextState = data.redirect or 'event'
        @$state.go nextState, data

module.exports = LoginCtrl