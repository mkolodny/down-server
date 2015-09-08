require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/asteroid/asteroid-module'
EventCtrl = require './event-controller'

describe 'login controller', ->
  $state = null
  $stateParams = null
  $q = null
  $rootScope = null
  Auth = null
  Asteroid = null
  ctrl = null
  linkId = null
  event = null
  fromUser = null
  invitation = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.asteroid')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $state = $injector.get '$state'
    $stateParams = $injector.get '$stateParams'
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    Auth = angular.copy $injector.get('Auth')
    Asteroid = $injector.get 'Asteroid'

    event =
      id: 123
    fromUser =
      id: 456
    $stateParams =
      event: event
      fromUser: fromUser

    ctrl = $controller EventCtrl,
      Auth: Auth
      $stateParams: $stateParams
  )
