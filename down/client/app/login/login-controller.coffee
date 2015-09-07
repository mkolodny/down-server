class LoginCtrl
  constructor: (@$state, @$stateParams, @$window, @Auth, @EventService) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser

  login: ->
    @$window.FB.login @handleFBLogin

  handleFBLogin: (response) =>
    accessToken = response.authResponse?.accessToken
    if accessToken
      @Auth.authWithFacebook(accessToken)
        .then =>
          @EventService.getData()
        .then (data) =>
          nextState = data.redirect or 'event'
          @$state.go nextState, data



module.exports = LoginCtrl