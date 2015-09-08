class EventCtrl
  constructor: (@$state, @$stateParams) ->
    redirectView = @$stateParams.redirectView
    if redirectView
      @$state.go redirectView, @$stateParams


module.exports = EventCtrl