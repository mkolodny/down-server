require 'angular'
require 'angular-ui-router'
require './event/event-module'

angular.module 'down', [
    'ui.router'
    'down.event'
  ]
  .config ($httpProvider, $locationProvider, $urlRouterProvider, $stateProvider) ->
    # Use html5 push state.
    $locationProvider.html5Mode true

    # Set a catch-all state.
    $urlRouterProvider.otherwise '/'

    # Look for the CSRF cookie, and add it to the headers.
    $httpProvider.defaults.xsrfCookieName = 'csrftoken'
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken'
