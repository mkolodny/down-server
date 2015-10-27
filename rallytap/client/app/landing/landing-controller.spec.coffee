require 'angular'
require 'angular-mocks'
require 'down-ionic/app/common/meteor/meteor-mocks'
LandingCtrl = require './landing-controller'

describe 'landing controller', ->
  $window = null
  ctrl = null
  scope = null

  beforeEach angular.mock.module('angular-meteor')

  beforeEach inject(($injector) ->
    $controller = $injector.get '$controller'
    $window = $injector.get '$window'
    scope = $injector.get '$rootScope'

    ctrl = $controller LandingCtrl,
      $scope: scope
  )

  describe 'sending a download link', ->
    downloadPhone = null

    beforeEach ->
      scope.sendSMSForm =
        $valid: true
      $window.branch =
        sendSMS: jasmine.createSpy 'branch.sendSMS'
      downloadPhone = '+19252852230'
      ctrl.downloadPhone = downloadPhone

      ctrl.sendSMS()

    it 'should send the sms', ->
      linkData =
        channel: 'WebView'
        feature: 'Text-To-Download'
      expect($window.branch.sendSMS).toHaveBeenCalledWith downloadPhone, linkData

    it 'should clear the form', ->
      expect(ctrl.downloadPhone).toBeNull()
