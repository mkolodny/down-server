require 'angular'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
InvitationCtrl = require './invitation-controller'

angular.module 'rallytapWeb.invitation', [
    'ui.router'
    'rallytap.auth'
    'rallytap.resources'
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
