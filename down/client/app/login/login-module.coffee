require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
LoginCtrl = require './login-controller'

angular.module 'down.login', [
    'ui.router'
    'down.auth'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'login',
        url: '/login'
        templateUrl: '/partials/login/login.html'
        controller: 'LoginCtrl as login'
        params:
        	event: null
          fromUser: null
          linkId: null
          invitation: null
  .controller 'LoginCtrl', LoginCtrl
