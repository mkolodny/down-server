class EventCtrl
  constructor: (@$state, @$stateParams) ->
    redirectView = @$stateParams.redirectView
    if redirectView
      @$state.go redirectView, @$stateParams
      return

    @event = @$stateParams.event
    @invitation = @$stateParams.invitation


module.exports = EventCtrl