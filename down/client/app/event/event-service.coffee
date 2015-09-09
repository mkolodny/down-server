class EventService
  constructor: (@$q, @$state, @Auth, @Invitation, @LinkInvitation) ->

  getData: (params) ->
    deferred = @$q.defer()

    if (['event', 'fromUser', 'invitation'].every (key) => params[key] isnt null)
      return {
        event: params.event
        fromUser: params.fromUser
        invitation: params.invitation
        linkId: params.linkId
      }

    @Auth.isAuthenticated()
      .then (isAuthenticated) =>
        if isAuthenticated
          @LinkInvitation.getByLinkId {linkId: params.linkId}
        else
          {redirectView: 'login', linkId: params.linkId}
      .then (data) =>
        nonMemberResponses = [@Invitation.noResponse, @Invitation.declined]
        if data.invitation?.response in nonMemberResponses
          data.redirectView = 'invitation'
          data.linkId = params.linkId
        deferred.resolve data
      , ->
        deferred.resolve {error: true}

    deferred.promise

module.exports = EventService
