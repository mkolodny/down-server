require 'angular'
require 'angular-ui-router'
InvitationCtrl = require './invitation-controller'

angular.module 'down.invitation', [
    'ui.router'
  ]
  .config ($stateProvider) ->
    $stateProvider
      .state 'invitation',
        url: '/i/:linkId'
        templateUrl: '/partials/invitation/invitation.html'
        controller: 'InvitationCtrl as invitation'
        params:
          event: null
          fromUser: null
          invitation: null
          linkId: null
  .controller 'InvitationCtrl', InvitationCtrl
