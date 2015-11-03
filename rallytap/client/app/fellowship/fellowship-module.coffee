require 'angular'
require 'angular-ui-router'
FellowshipCtrl = require './fellowship-controller'

angular.module 'rallytapWeb.fellowship', [
    'ui.router'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'fellowship',
        url: '/fellowship'
        templateUrl: '/partials/fellowship/fellowship.html'
        controller: 'FellowshipCtrl as fellowship'
  .controller 'FellowshipCtrl', FellowshipCtrl
