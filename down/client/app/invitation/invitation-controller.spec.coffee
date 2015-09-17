require 'angular'
require 'angular-mocks'
require 'angular-ui-router'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
InvitationCtrl = require './invitation-controller'

describe 'invitation controller', ->
  $q = null
  $state = null
  $stateParams = null
  Auth = null
  Invitation = null
  ctrl = null
  event = null
  fromUser = null
  invitation = null
  linkId = null
  scope = null

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.resources')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $q = $injector.get '$q'
    $state = $injector.get '$state'
    $stateParams = $injector.get '$stateParams'
    Auth = angular.copy $injector.get('Auth')
    Invitation = $injector.get 'Invitation'
    scope = $injector.get '$rootScope'

    event =
      id: 1
    fromUser =
      id: 2
    invitation =
      id: 3
    linkId = '123'
    $stateParams =
      event: event
      fromUser: fromUser
      invitation: invitation
      linkId: linkId

    ctrl = $controller InvitationCtrl,
      Auth: Auth
      $stateParams: $stateParams
  )

  it 'should set the event on the controller', ->
    expect(ctrl.event).toBe event

  it 'should set the from user on the controller', ->
    expect(ctrl.fromUser).toBe fromUser

  it 'should set the invitation on the controller', ->
    expect(ctrl.invitation).toBe invitation

  it 'should set the current user on the controller', ->
    expect(ctrl.currentUser).toBe Auth.user

  describe 'checking whether the user accepted their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        invitation.response = Invitation.accepted

      it 'should return true', ->
        expect(ctrl.wasAccepted()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        invitation.response = Invitation.maybe

      it 'should return false', ->
        expect(ctrl.wasAccepted()).toBe false


  describe 'checking whether the user responded maybe their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        invitation.response = Invitation.maybe

      it 'should return true', ->
        expect(ctrl.wasMaybed()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        invitation.response = Invitation.accepted

      it 'should return false', ->
        expect(ctrl.wasMaybed()).toBe false


  describe 'checking whether the user declined their invitation', ->

    describe 'when they did', ->

      beforeEach ->
        invitation.response = Invitation.declined

      it 'should return true', ->
        expect(ctrl.wasDeclined()).toBe true


    describe 'when they didn\'t', ->

      beforeEach ->
        invitation.response = Invitation.maybe

      it 'should return false', ->
        expect(ctrl.wasDeclined()).toBe false



  describe 'responding to the invitation', ->
    response = null
    deferred = null

    beforeEach ->
      # Mock the current invitation response.
      response = Invitation.maybe
      invitation.response = response

      deferred = $q.defer()
      spyOn(Invitation, 'updateResponse').and.returnValue
        $promise: deferred.promise
      spyOn $state, 'go'

      ctrl.respondToInvitation response

    it 'should update the invitation', ->
      expect(Invitation.updateResponse).toHaveBeenCalledWith invitation, response

    describe 'successfully', ->

      beforeEach ->
        deferred.resolve()
        scope.$apply()

      it 'should go to the event view', ->
        expect($state.go).toHaveBeenCalledWith 'event',
          event: event
          fromUser: fromUser
          invitation: invitation
          linkId: linkId


    describe 'unsuccessfully', ->

      beforeEach ->
        deferred.reject()
        scope.$apply()

      it 'show an error', ->
        error = 'For some reason, that didn\'t work.'
        expect(ctrl.error).toBe error


  describe 'accepting the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.acceptInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.accepted


  describe 'responding maybe to the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.maybeInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.maybe


  describe 'declining the invitation', ->

    beforeEach ->
      spyOn ctrl, 'respondToInvitation'

      ctrl.declineInvitation()

    it 'should respond to the invitation', ->
      expect(ctrl.respondToInvitation).toHaveBeenCalledWith Invitation.declined
