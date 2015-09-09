class EventService
  constructor: (@$q, @$state, @$stateParams, @Auth, @Invitation, @LinkInvitation) ->

  getData: ->
    deferred = @$q.defer()

    if (['event', 'fromUser', 'invitation'].every (key) => key of @$stateParams)
      return {
        event: @$stateParams.event
        fromUser: @$stateParams.fromUser
        invitation: @$stateParams.invitation
      }

    @Auth.isAuthenticated()
      .then (isAuthenticated) =>
        if isAuthenticated
          @LinkInvitation.getByLinkId {linkId: @$stateParams.linkId}
        else
          {redirectView: 'login'}
      .then (data) =>
        nonMemberResponses = [@Invitation.noResponse, @Invitation.declined]
        if data.invitation?.response in nonMemberResponses
          data.redirectView = 'invitation'
        deferred.resolve data
      , ->
        deferred.resolve {error: true}

    deferred.promise

module.exports = EventService
