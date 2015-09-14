class InvitationCtrl
  constructor: (@$state, @$stateParams, @Auth, @Invitation) ->
    @event = @$stateParams.event
    @fromUser = @$stateParams.fromUser
    @invitation = @$stateParams.invitation
    @currentUser = @Auth.user

  wasAccepted: ->
    @invitation.response is @Invitation.accepted

  wasMaybed: ->
    @invitation.response is @Invitation.maybe

  wasDeclined: ->
    @invitation.response is @Invitation.declined

  acceptInvitation: ->
    @respondToInvitation @Invitation.accepted

  maybeInvitation: ->
    @respondToInvitation @Invitation.maybe

  declineInvitation: ->
    @respondToInvitation @Invitation.declined

  respondToInvitation: (response) ->
    @Invitation.updateResponse @invitation, response
      .$promise.then =>
        @$state.go 'event',
          event: @event
          fromUser: @fromUser
          invitation: @invitation
          linkId: @$stateParams.linkId
      , =>
        @error = 'For some reason, that didn\'t work.'

module.exports = InvitationCtrl
