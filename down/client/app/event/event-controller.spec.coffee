require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/asteroid/asteroid-module'
EventCtrl = require './event-controller'

describe 'login controller', ->
  $controller = null
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
    invitation =
      id: 789
    $stateParams =
      event: event
      fromUser: fromUser
      invitation: invitation

    ctrl = $controller EventCtrl,
      Auth: Auth
      $stateParams: $stateParams
  )

  describe 'when there is a redirect', ->
    redirectView = null

    beforeEach ->
      redirectView = 'login'
      $stateParams.redirectView = redirectView

      spyOn $state, 'go'

      ctrl = $controller EventCtrl,
        Auth: Auth
        $stateParams: $stateParams

    it 'should go to the redirect state', ->
      expect($state.go).toHaveBeenCalledWith redirectView, $stateParams


  it 'should set the event on the controller', ->
    expect(ctrl.event).toBe event

  it 'should set the invitation on the controller', ->
    expect(ctrl.invitation).toBe invitation


