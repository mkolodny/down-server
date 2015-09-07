require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
LoginCtrl = require './login-controller'

describe 'login controller', ->
  $state = null
  $q = null
  $rootScope = null
  $window = null
  Auth = null
  ctrl = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $state = $injector.get '$state'
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    $window = $injector.get '$window'
    Auth = angular.copy $injector.get('Auth')

    ctrl = $controller LoginCtrl,
      Auth: Auth
  )

  describe 'logging in', ->

    beforeEach ->
      $window.FB =
        login: jasmine.createSpy('FB.login')
      ctrl.login()

    it 'should call login with the Facebook SDK', ->
      expect($window.FB.login).toHaveBeenCalledWith ctrl.handleFBLogin


  describe 'handling Facebook login response', ->

    describe 'when user completes facebook oauth', ->
      accessToken = null
      defered = null

      beforeEach ->
        accessToken = '1234'
        response =
          authResponse:
            accessToken: accessToken

        defered = $q.defer()
        spyOn(Auth, 'authWithFacebook').and.returnValue defered.promise

        ctrl.handleFBLogin response

      it 'should auth user with accessToken', ->
        expect(Auth.authWithFacebook).toHaveBeenCalledWith accessToken

      describe 'when authentication is successful', ->

        it 'should get the link invitation', ->



      describe 'on authentication fails', ->

        xit 'should show an error', ->


    describe 'when user cancels facebook login process', ->

      xit 'should show an error', ->