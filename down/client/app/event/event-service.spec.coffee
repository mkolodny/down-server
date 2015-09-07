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
      linkId = null
      deferredLinkInvitation = null
      data = null

      beforeEach ->
        linkId = 1
        $stateParams.linkId = linkId
        deferredLinkInvitation = $q.defer()
        spyOn(LinkInvitation, 'getByLinkId').and.returnValue
          $promise: deferredLinkInvitation.promise
        deferredAuth = $q.defer()

        rejected = false
        EventService.getData()
          .then (_data_) ->
            data = _data_

      afterEach ->
        delete $stateParams.linkId

      it 'should get the link invitation', ->
        expect(LinkInvitation.getByLinkId).toHaveBeenCalledWith {linkId: linkId}

      describe 'when the link invitation returns successfully', ->
        linkInvitation = null

        beforeEach ->
          linkInvitation =
            event: event
            eventId: event.id
            fromUser: fromUser
            fromUserId: fromUser.id
            invitation: invitation
            invitationId: invitation.id
          deferredLinkInvitation.resolve linkInvitation
          $rootScope.$apply()

        it 'should check whether the user is logged in', ->
          expect(Auth.isAuthenticated).toHaveBeenCalled()

        describe 'when the user is logged in', ->

          beforeEach ->
            deferredLinkInvitation = $q.defer()
            deferredAuth = $q.defer()

            EventService.getData()
              .then (_data_) ->
                data = _data_

          describe 'and the user hasn\'t responded yet', ->

            beforeEach ->
              linkInvitation.invitation.response = Invitation.noResponse

              deferredLinkInvitation.resolve linkInvitation
              deferredAuth.resolve true
              $rootScope.$apply()

            it 'should redirect to the invitation view', ->
              expect(data).toEqual
                event: event
                fromUser: fromUser
                invitation: invitation
                redirectView: 'invitation'


          describe 'and the user declined their invitation', ->

            beforeEach ->
              invitation.response = Invitation.declined

              deferredLinkInvitation.resolve linkInvitation
              deferredAuth.resolve true
              $rootScope.$apply()

            it 'should redirect to the invitation view', ->
              expect(data).toEqual
                event: event
                fromUser: fromUser
                invitation: invitation
                redirectView: 'invitation'


        describe 'when the user isn\'t logged in', ->

          beforeEach ->
            deferredLinkInvitation = $q.defer()
            deferredAuth = $q.defer()

            EventService.getData()
              .then (_data_) ->
                data = _data_
            deferredLinkInvitation.resolve linkInvitation
            deferredAuth.resolve false
            $rootScope.$apply()

          it 'should redirect to the login view', ->
            expect(data).toEqual
              event: event
              fromUser: fromUser
              invitation: invitation
              redirectView: 'login'


        describe 'when the is authenticated request fails', ->

          beforeEach ->
            deferredAuth.reject()
            $rootScope.$apply()

          it 'should return null', ->
            expect(data).toBeNull()


      describe 'when the link invitation request fails', ->

        beforeEach ->
          deferredLinkInvitation.reject()
          $rootScope.$apply()

        it 'should return null', ->
          expect(data).toBeNull()
