class LoginCtrl
  constructor: (@$window, @Auth) ->

  login: ->
    @$window.FB.login @handleFBLogin

  handleFBLogin: (response) =>
    accessToken = response.authResponse?.accessToken
    if accessToken
      @Auth.authWithFacebook(accessToken)
        


module.exports = LoginCtrl