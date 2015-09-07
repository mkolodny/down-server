require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require '../event/event-module'
LoginCtrl = require './login-controller'

describe 'login controller', ->
  $state = null
  $stateParams = null
  $q = null
  $rootScope = null
  $window = null
  Auth = null
  EventService = null
  ctrl = null
  event = null
  fromUser = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.event')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $state = $injector.get '$state'
    $stateParams = $injector.get '$stateParams'
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    $window = $injector.get '$window'
    Auth = angular.copy $injector.get('Auth')
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
        eventDeferred = null

        beforeEach ->
          eventDeferred = $q.defer()
          spyOn(EventService, 'getData').and.returnValue eventDeferred.promise
        
          defered.resolve()
          $rootScope.$apply()

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

              eventDeferred.resolve eventData
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

              eventDeferred.resolve eventData
              $rootScope.$apply()

            it 'should go to the invitation view', ->
              expect($state.go).toHaveBeenCalledWith 'invitation', eventData


        describe 'when there is an error getting event data', ->

          xit 'should show an error', ->


      describe 'on authentication fails', ->

        xit 'should show an error', ->


    describe 'when user cancels facebook login process', ->

      xit 'should show an error', ->