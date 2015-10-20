class LandingCtrl
  @$inject: ['$scope', '$window']
  constructor: (@$scope, @$window) ->

  sendSMS: ->
    if not @$scope.sendSMSForm.$valid then return

    linkData =
      channel: 'WebView'
      feature: 'Text-To-Download'
    @$window.branch.sendSMS @downloadPhone, linkData
    @downloadPhone = null

module.exports = LandingCtrl
