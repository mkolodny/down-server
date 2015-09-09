require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require './event/event-module'
require './login/login-module'
require './invitation/invitation-module'

angular.module 'down', [
    'ui.router'
    'down.auth'
    'down.event'
    'down.login'
    'down.invitation'
  ]
  .config ($httpProvider, $locationProvider, $urlRouterProvider, $stateProvider) ->
    # Use html5 push state.
    $locationProvider.html5Mode
      enabled: true
      requireBase: false

    # Set a catch-all state.
    $urlRouterProvider.otherwise '/'

    # Expect JSON from the server.
    acceptHeader = 'application/json; version=1.2'
    $httpProvider.defaults.headers.common['Accept'] = acceptHeader

    # Include the Authorization header in each request.
    $httpProvider.interceptors.push ($injector) ->
      request: (config) ->
        # Delay injecting the $http + Auth services to avoid a circular
        #   dependency.
        Auth = $injector.get 'Auth'
        if Auth.user.authtoken?
          authHeader = "Token #{Auth.user.authtoken}"
          config.headers.Authorization = authHeader
        config
