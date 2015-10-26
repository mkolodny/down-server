require 'angular'
require 'angular-mocks'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
Service = require './event-service'

describe 'event service', ->
  $q = null
  $rootScope = null
  Auth = null
  EventService = null
  Invitation = null
  LinkInvitation = null
  deferredAuth = null
  getMe = null
  event = null
  fromUser = null
  invitation = null
  linkId = null

  beforeEach angular.mock.module('rallytap.auth')

  beforeEach angular.mock.module('rallytap.resources')

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module(($provide) ->
    $provide.service 'EventService', Service

    Auth =
      user:
        id: 1
      getMe: jasmine.createSpy('Auth.getMe').and.callFake ->
        deferredAuth.promise
    $provide.value 'Auth', Auth
    return
  )

  beforeEach inject(($injector) ->
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    Auth = angular.copy $injector.get('Auth')
    EventService = $injector.get 'EventService'
    Invitation = $injector.get 'Invitation'
    LinkInvitation = $injector.get 'LinkInvitation'
    event =
      id: 1
    fromUser =
      id: 2
    invitation =
      id: 3
    linkId = '123'
  )

  describe 'getting initial data', ->
    params = null

    describe 'when we already have data', ->
      data = null

      beforeEach ->
        params =
          event: event
          fromUser: fromUser
          invitation: invitation
          linkId: linkId
        data = EventService.getData params

      it 'should return the data from params', ->
        expect(data).toEqual
          event: event
          fromUser: fromUser
          invitation: invitation
          linkId: linkId


    describe 'when we don\'t have data yet', ->
      data = null

      beforeEach ->
        deferredAuth = $q.defer()

        params =
          event: null
          fromUser: null
          invitation: null
          linkId: linkId
        EventService.getData params
          .then (_data_) ->
            data = _data_

      it 'should check if the user is logged in', ->
        expect(Auth.getMe).toHaveBeenCalled()

      describe 'when the user is logged in', ->
        deferredLinkInvitation = null
        user = null

        beforeEach ->
          user = id: 1
          deferredLinkInvitation = $q.defer()
          spyOn(LinkInvitation, 'getByLinkId').and.returnValue
            $promise: deferredLinkInvitation.promise

          deferredAuth.resolve user
          $rootScope.$apply()

        it 'should get the link invitation', ->
          expect(LinkInvitation.getByLinkId).toHaveBeenCalledWith {linkId: linkId}

        it 'should set the user on auth', ->
          expect(Auth.user).toBe user

        describe 'getting the link invitation successfully', ->
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

              deferredLinkInvitation.resolve linkInvitation
              $rootScope.$apply()

            it 'should resolve the promise with the linkInvitation', ->
              expect(data).toEqual linkInvitation


          describe 'when the user responded maybe to their invitation', ->

            beforeEach ->
              linkInvitation.invitation.response = Invitation.maybe

              deferredLinkInvitation.resolve linkInvitation
              $rootScope.$apply()

            it 'should resolve the promise with the linkInvitation', ->
              expect(data).toEqual linkInvitation


          describe 'when the user declined their invitation', ->

            beforeEach ->
              linkInvitation.invitation.response = Invitation.declined

              deferredLinkInvitation.resolve linkInvitation
              $rootScope.$apply()

            it 'should resolve the promise with a redirect view', ->
              expect(data).toEqual angular.extend({}, linkInvitation,
                redirectView: 'invitation'
                linkId: linkId
              )


          describe 'when the user hasn\'t responded to their invitation', ->

            beforeEach ->
              linkInvitation.invitation.response = Invitation.noResponse

              deferredLinkInvitation.resolve linkInvitation
              $rootScope.$apply()

            it 'should resolve the promise with a redirect view', ->
              expect(data).toEqual angular.extend({}, linkInvitation,
                redirectView: 'invitation'
                linkId: linkId
              )


        describe 'getting the link invitation fails', ->

          beforeEach ->
            deferredLinkInvitation.reject()
            $rootScope.$apply()

          it 'should resolve the promise with an error', ->
            expect(data).toEqual {error: true}


      describe 'when the user isn\'t logged in', ->
        deferredLinkInvitation = null

        beforeEach ->
          deferredLinkInvitation = $q.defer()
          spyOn(LinkInvitation, 'getByLinkId').and.returnValue
            $promise: deferredLinkInvitation.promise

          deferredAuth.reject {status: 401}
          $rootScope.$apply()

        describe 'getting the link invitation', ->
          linkInvitation = null

          beforeEach ->
            console.log 'yo!'
            linkInvitation =
              event:
                id: 1
              fromUser:
                id: 2
              invitation:
                id: 3
            deferredLinkInvitation.resolve linkInvitation
            $rootScope.$apply()

          it 'should resolve the promise with a redirect view', ->
            expect(data).toEqual angular.extend({}, linkInvitation,
              redirectView: 'login'
              linkId: linkId
            )


      describe 'when checking whether the user is logged in fails', ->

        beforeEach ->
          deferredAuth.reject()
          $rootScope.$apply()

        it 'should resolve the promise with an error', ->
          expect(data.error).toBe true
