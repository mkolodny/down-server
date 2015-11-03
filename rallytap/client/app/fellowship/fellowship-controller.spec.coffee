require 'angular'
require 'angular-mocks'
FellowshipCtrl = require './fellowship-controller'

describe 'invitation controller', ->
  $q = null
  $state = null
  $stateParams = null
  $httpBackend = null
  ctrl = null
  scope = null

  beforeEach angular.mock.module('rallytap.env')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $httpBackend = $injector.get '$httpBackend'
    $q = $injector.get '$q'
    scope = $injector.get '$rootScope'

    ctrl = $controller FellowshipCtrl
  )

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()

  describe 'submitting the application', ->
    url = null
    beforeEach ->
      ctrl.username = 'a'
      ctrl.school = 'The Dopest School In NYC'
      url = "#{ctrl.apiRoot}/fellowship-applications"

    it 'should POST the data', ->
      postData =
        username: ctrl.username
        school: ctrl.school

      $httpBackend.expectPOST url, postData
        .respond 201, true

      ctrl.submit()
      $httpBackend.flush 1

