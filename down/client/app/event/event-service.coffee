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

    linkInvitation = null
    params = null
    @LinkInvitation.getByLinkId {linkId: @$stateParams.linkId}
      .$promise.then (_linkInvitation_) =>
        linkInvitation = _linkInvitation_
        params =
          event: linkInvitation.event
          fromUser: linkInvitation.fromUser
          invitation: linkInvitation.invitation
          linkId: @$stateParams.linkId
        @Auth.isAuthenticated()
      .then (isAuthenticated) =>
        if isAuthenticated
          nonMemberResponses = [@Invitation.noResponse, @Invitation.declined]
          if linkInvitation.invitation.response in nonMemberResponses
            angular.extend params,
              redirectView: 'invitation'
        else
            angular.extend params,
              redirectView: 'login'
        deferred.resolve params
      , ->
        deferred.resolve null

    deferred.promise

module.exports = EventService
