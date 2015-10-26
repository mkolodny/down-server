require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
LoginCtrl = require './login-controller'

angular.module 'rallytapWeb.login', [
    'ui.router'
    'rallytap.auth'
    'rallytap.resources'
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
  .controller 'LoginCtrl', LoginCtrl
