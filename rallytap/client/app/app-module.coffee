require 'angular'
require 'angular-ui-router'
require 'angular-local-storage'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/asteroid/asteroid-module'
require 'down-ionic/app/common/resources/resources-module'
require './event/event-module'
require './login/login-module'
require './invitation/invitation-module'
require './landing/landing-module'

angular.module 'down', [
    'ui.router'
    'down.auth'
    'down.asteroid'
    'down.event'
    'down.landing'
    'down.login'
    'down.invitation'
    'down.resources'
    'LocalStorageModule'
  ]
  .config ($httpProvider, $locationProvider, $urlRouterProvider,
           $stateProvider) ->
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
  .run (localStorageService, Auth, User, Asteroid) ->
    # Check local storage for currentUser and currentPhone
    currentUser = localStorageService.get 'currentUser'
    if currentUser isnt null
      Auth.user = new User currentUser
      Asteroid.login() # re-establish asteroid auth
      for id, friend of Auth.user.friends
        Auth.user.friends[id] = new User friend
      for id, friend of Auth.user.facebookFriends
        Auth.user.facebookFriends[id] = new User friend
