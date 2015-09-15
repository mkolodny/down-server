require 'angular'
require 'angularjs-scroll-glue'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
require 'down-ionic/app/common/intl-phone/intl-phone-module'
EventCtrl = require './event-controller'
EventService = require './event-service'

angular.module 'down.event', [
    'ui.router'
    'down.auth'
    'down.intlPhone'
    'down.resources'
    'luegg.directives'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'event',
        url: '/e/:linkId'
        templateUrl: '/partials/event/event.html'
        controller: 'EventCtrl as event'
        params:
          linkId: null
          event: null
          fromUser: null
          invitation: null
          redirectView: null
        resolve:
          data: ['$stateParams', 'EventService', ($stateParams, EventService) ->
            EventService.getData $stateParams
          ]
  .controller 'EventCtrl', EventCtrl
  .service 'EventService', EventService
