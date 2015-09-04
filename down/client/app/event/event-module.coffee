require 'angular'
require 'angular-ui-router'
EventCtrl = require './event-controller'

angular.module 'down.event', [
    'ui.router'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'event',
        url: '/'
        templateUrl: '/partials/event/event.html'
        controller: 'EventCtrl as event'
  .controller 'EventCtrl', EventCtrl
