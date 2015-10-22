require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/intl-phone/intl-phone-module'
LandingCtrl = require './landing-controller'

angular.module 'rallytapWeb.landing', [
    'ui.router'
    'rallytapWeb.intlPhone'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'landing',
        url: '/'
        templateUrl: '/partials/landing/landing.html'
        controller: 'LandingCtrl as landing'
  .controller 'LandingCtrl', LandingCtrl
