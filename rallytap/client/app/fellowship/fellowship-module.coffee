require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/env/env-module'
FellowshipCtrl = require './fellowship-controller'

angular.module 'rallytapWeb.fellowship', [
    'ui.router'
    'rallytap.env'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'fellowship',
        url: '/fellowship'
        templateUrl: '/partials/fellowship/fellowship.html'
        controller: 'FellowshipCtrl as fellowship'
  .controller 'FellowshipCtrl', FellowshipCtrl
