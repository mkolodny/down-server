require 'angular'
require 'angular-local-storage'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/meteor/meteor-mocks'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
LoginCtrl = require './login-controller'

describe 'login controller', ->
  $meteor = null
  $q = null
  $rootScope = null
  $state = null
  $stateParams = null
  $window = null
  Auth = null
  Invitation = null
  LinkInvitation = null
  localStorage = null
  ctrl = null
  event = null
  fromUser = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('angular-meteor')

  beforeEach angular.mock.module('rallytap.auth')

  beforeEach angular.mock.module('rallytap.resources')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $meteor = $injector.get '$meteor'
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    $state = $injector.get '$state'
    $stateParams = $injector.get '$stateParams'
    $window = $injector.get '$window'
    Auth = $injector.get 'Auth'
    Invitation = $injector.get 'Invitation'
    LinkInvitation = $injector.get 'LinkInvitation'
    localStorage = $injector.get 'localStorageService'

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

  it 'should set the event on the controller', ->
    expect(ctrl.event).toEqual event

  it 'should set the from user on the controller', ->
    expect(ctrl.fromUser).toEqual fromUser

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
      deferred = null

      beforeEach ->
        accessToken = '1234'
        response =
          authResponse:
            accessToken: accessToken

        deferred = $q.defer()
        spyOn(Auth, 'facebookLogin').and.returnValue deferred.promise

        ctrl.handleFBLogin response

      it 'should log the user in with accessToken', ->
        expect(Auth.facebookLogin).toHaveBeenCalledWith accessToken

      describe 'when authentication is successful', ->
        user = null

        beforeEach ->
          spyOn ctrl, 'meteorLogin'

          user =
            id: 1
          deferred.resolve user
          $rootScope.$apply()

        it 'should call meteorLogin', ->
          expect(ctrl.meteorLogin).toHaveBeenCalledWith user


      describe 'when authentication fails', ->

        beforeEach ->
          deferred.reject()
          $rootScope.$apply()

        it 'should show an error', ->
          expect(ctrl.loginFailed).toBe true


    describe 'when user cancels facebook login process', ->

      beforeEach ->
        ctrl.handleFBLogin {}

      it 'should show an error', ->
        expect(ctrl.fbLoginCanceled).toBe true


  describe 'logging into the meteor server', ->
    deferred = null
    user = null

    beforeEach ->
      deferred = $q.defer()
      $meteor.loginWithPassword.and.returnValue deferred.promise

      user =
        id: 1
        email: 'aturing@gmail.com'
        authtoken: '1234'
      ctrl.meteorLogin user

    it 'should attempt to login', ->
      expect($meteor.loginWithPassword).toHaveBeenCalledWith("#{user.id}",
          user.authtoken)

    describe 'successfully', ->

      beforeEach ->
        spyOn ctrl, 'getLinkData'
        spyOn Auth, 'setUser'

        deferred.resolve()
        $rootScope.$apply()

      afterEach ->
        localStorage.clearAll()

      it 'should set the user on auth', ->
        expect(Auth.user).toAngularEqual user

      it 'should save the user in local storage', ->
        expect(localStorage.get 'currentUser').toEqual user

      it 'should get the link data', ->
        expect(ctrl.getLinkData).toHaveBeenCalled()


    describe 'unsuccessfully', ->

      beforeEach ->
        deferred.reject()
        $rootScope.$apply()

      it 'should show an error', ->
        expect(ctrl.error).toBe 'Oops, something went wrong.'


  describe 'getting the link data', ->
    linkId = null
    deferred = null

    beforeEach ->
      linkId = '123'
      $stateParams.linkId = linkId
      deferred = $q.defer()
      spyOn(LinkInvitation, 'getByLinkId').and.returnValue
        $promise: deferred.promise

      ctrl.getLinkData()

    it 'should get the link invitation', ->
      expect(LinkInvitation.getByLinkId).toHaveBeenCalledWith {linkId: linkId}

    describe 'when event data is returned successfully', ->
      linkInvitation = null

      beforeEach ->
        linkInvitation =
          event:
            id: 1
          fromUser:
            id: 2
          invitation:
            id: 3

      describe 'when the user accepted their invitation', ->

        beforeEach ->
          linkInvitation.invitation.response = Invitation.accepted
          spyOn $state, 'go'

          deferred.resolve linkInvitation
          $rootScope.$apply()

        it 'should go to the event view', ->
          expect($state.go).toHaveBeenCalledWith 'event', linkInvitation


      describe 'when the user responded maybe to their invitation', ->

        beforeEach ->
          linkInvitation.invitation.response = Invitation.maybe
          spyOn $state, 'go'

          deferred.resolve linkInvitation
          $rootScope.$apply()

        it 'should go to the event view', ->
          expect($state.go).toHaveBeenCalledWith 'event', linkInvitation


      describe 'when the user declined their invitation', ->

        beforeEach ->
          linkInvitation.invitation.response = Invitation.declined
          spyOn $state, 'go'

          deferred.resolve linkInvitation
          $rootScope.$apply()

        it 'should go to the invitation view', ->
          expect($state.go).toHaveBeenCalledWith 'invitation', linkInvitation


      describe 'when the user hasn\'t responded to their invitation', ->

        beforeEach ->
          linkInvitation.invitation.response = Invitation.noResponse
          spyOn $state, 'go'

          deferred.resolve linkInvitation
          $rootScope.$apply()

        it 'should go to the invitation view', ->
          expect($state.go).toHaveBeenCalledWith 'invitation', linkInvitation


    describe 'when there is an error getting event data', ->

      beforeEach ->
        deferred.reject()
        $rootScope.$apply()

      it 'should show an error', ->
        expect(ctrl.fetchInvitationError).toBe true
