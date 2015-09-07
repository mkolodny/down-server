require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/asteroid/asteroid-module'
require '../event/event-module'
LoginCtrl = require './login-controller'

describe 'login controller', ->
  $state = null
  $stateParams = null
  $q = null
  $rootScope = null
  $window = null
  Auth = null
  Asteroid = null
  EventService = null
  ctrl = null
  event = null
  fromUser = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.event')

  beforeEach angular.mock.module('down.asteroid')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $state = $injector.get '$state'
    $stateParams = $injector.get '$stateParams'
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    $window = $injector.get '$window'
    Auth = angular.copy $injector.get('Auth')
    Asteroid = $injector.get 'Asteroid'
    EventService = $injector.get 'EventService'

    event =
      id: 123
    fromUser =
      id: 456
    $stateParams =
      event: event
      fromUser: fromUser

    ctrl = $controller LoginCtrl,
      Auth: Auth
      $stateParams: $stateParams
  )

  it 'should set the linkId on the controller', ->
    expect(ctrl.event).toEqual event

  it 'should set the event on the controller', ->
    expect(ctrl.fromUser).toEqual fromUser

  describe 'initializing the facebook sdk', ->
    fbAppId = null

    beforeEach ->
      fbAppId = '864552050271610'
      $window.fbAppId = '864552050271610'
      $window.FB =
        init: jasmine.createSpy 'FB.init'

      $window.fbAsyncInit()

    it 'should call FB.init', ->
      initOptions =
        appId: fbAppId
        xfbml: true
        version: 'v2.3'
      expect($window.FB.init).toHaveBeenCalledWith initOptions


  describe 'logging in', ->

    beforeEach ->
      $window.FB =
        login: jasmine.createSpy 'FB.login'
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
        user = null

        beforeEach ->
          spyOn ctrl, 'meteorLogin'
        
          user =
            id: 1
          defered.resolve user
          $rootScope.$apply()

        it 'should call meteorLogin', ->
          expect(ctrl.meteorLogin).toHaveBeenCalledWith user


      describe 'on authentication fails', ->

        xit 'should show an error', ->


    describe 'when user cancels facebook login process', ->

      xit 'should show an error', ->


  describe 'logging into the meteor server', ->
    deferred = null
    user = null

    beforeEach ->
      deferred = $q.defer()
      spyOn(Asteroid, 'login').and.returnValue deferred.promise

      user =
        id: 1
        email: 'aturing@gmail.com'
      ctrl.meteorLogin user

    it 'should attempt to login', ->
      expect(Asteroid.login).toHaveBeenCalled()

    describe 'successfully', ->

      beforeEach ->
        spyOn ctrl, 'getLinkData'
        spyOn Auth, 'setUser'

        deferred.resolve()
        $rootScope.$apply()


      it 'should save the user', ->
        expect(Auth.setUser).toHaveBeenCalledWith user


    describe 'unsuccessfully', ->

      beforeEach ->
        deferred.reject()
        $rootScope.$apply()

      it 'should show an error', ->
        expect(ctrl.error).toBe 'Oops, something went wrong.'


  describe 'getting the link data', ->
    deferred = null

    beforeEach ->
      deferred= $q.defer()
      spyOn(EventService, 'getData').and.returnValue deferred.promise

      ctrl.getLinkData()

    it 'should get the link invitation', ->
      expect(EventService.getData).toHaveBeenCalled()

    describe 'when event data is returned successfully', ->
      
      describe 'when the user is a member of the event', ->
        eventData = null

        beforeEach ->
          eventData = 
            event:
              id: 1
            fromUser:
              id: 2
            invitation:
              id: 3

          spyOn $state, 'go'

          deferred.resolve eventData
          $rootScope.$apply()

        it 'should go to the event link view', ->
          expect($state.go).toHaveBeenCalledWith 'event', eventData


      describe 'when the user is a member of the event', ->
        eventData = null

        beforeEach ->
          eventData = 
            event:
              id: 1
            fromUser:
              id: 2
            invitation:
              id: 3
            redirect:
              'invitation'

          spyOn $state, 'go'

          deferred.resolve eventData
          $rootScope.$apply()

        it 'should go to the invitation view', ->
          expect($state.go).toHaveBeenCalledWith 'invitation', eventData


    describe 'when there is an error getting event data', ->

      xit 'should show an error', ->