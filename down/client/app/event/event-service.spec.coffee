require 'angular'
require 'angular-mocks'
require 'down-ionic/app/common/auth/auth-module'
require 'down-ionic/app/common/resources/resources-module'
require './event-module'

describe 'event service', ->
  $q = null
  $rootScope = null
  $stateParams = null
  Auth = null
  EventService = null
  Invitation = null
  LinkInvitation = null
  deferredAuth = null
  isAuthenticated = null
  event = null
  fromUser = null
  invitation = null

  beforeEach angular.mock.module('down.auth')

  beforeEach angular.mock.module('down.resources')

  beforeEach angular.mock.module('down.event')

  beforeEach angular.mock.module('ui.router')

  beforeEach angular.mock.module(($provide) ->
    Auth =
      user:
        id: 1
      isAuthenticated: jasmine.createSpy('Auth.isAuthenticated').and.callFake ->
        deferredAuth.promise
    $provide.value 'Auth', Auth
    return
  )

  beforeEach inject(($injector) ->
    $q = $injector.get '$q'
    $rootScope = $injector.get '$rootScope'
    $stateParams = $injector.get '$stateParams'
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
  )

  describe 'getting initial data', ->

    describe 'when we already have data', ->
      data = null

      beforeEach ->
        angular.extend $stateParams,
          event: event
          fromUser: fromUser
          invitation: invitation

        data = EventService.getData()

      afterEach ->
        for key in ['event', 'fromUser', 'invitation']
          delete $stateParams[key]

      it 'should return the data from $stateParams', ->
        expect(data).toEqual
          event: event
          fromUser: fromUser
          invitation: invitation


    describe 'when we don\'t have data yet', ->
      data = null

      beforeEach ->
        deferredAuth = $q.defer()

        EventService.getData()
          .then (_data_) ->
            data = _data_

      it 'should check if the user is logged in', ->
        expect(Auth.isAuthenticated).toHaveBeenCalled()

      describe 'when the user is logged in', ->
        linkId = null
        deferredLinkInvitation = null

        beforeEach ->
          linkId = '123'
          $stateParams.linkId = linkId

          deferredLinkInvitation = $q.defer()
          spyOn(LinkInvitation, 'getByLinkId').and.returnValue \
              deferredLinkInvitation.promise

          deferredAuth.resolve true
          $rootScope.$apply()

        afterEach ->
          delete $stateParams.linkId

        it 'should get the link invitation', ->
          expect(LinkInvitation.getByLinkId).toHaveBeenCalledWith {linkId: linkId}

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
              expectedData = angular.copy linkInvitation
              expectedData.redirectView = 'invitation'
              expect(data).toEqual expectedData


          describe 'when the user hasn\'t responded to their invitation', ->

            beforeEach ->
              linkInvitation.invitation.response = Invitation.noResponse

              deferredLinkInvitation.resolve linkInvitation
              $rootScope.$apply()

            it 'should resolve the promise with a redirect view', ->
              expectedData = angular.copy linkInvitation
              expectedData.redirectView = 'invitation'
              expect(data).toEqual expectedData


        describe 'getting the link invitation fails', ->

          beforeEach ->
            deferredLinkInvitation.reject()
            $rootScope.$apply()

          it 'should resolve the promise with an error', ->
            expect(data.error).toBe true


      describe 'when the user isn\'t logged in', ->

        beforeEach ->
          deferredAuth.resolve false
          $rootScope.$apply()

        it 'should resolve the promise with a redirect view', ->
          expect(data).toEqual {redirectView: 'login'}


      describe 'when checking whether the user is logged in fails', ->

        beforeEach ->
          deferredAuth.reject()
          $rootScope.$apply()

        it 'should resolve the promise with an error', ->
          expect(data.error).toBe true
