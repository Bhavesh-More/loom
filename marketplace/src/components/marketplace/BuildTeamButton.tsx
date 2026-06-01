import Icon from '../Icon'

type BuildTeamButtonProps = {
  onClick: () => void
}

function BuildTeamButton({ onClick }: BuildTeamButtonProps) {
  return (
    <button className="build-team-button" onClick={onClick} type="button">
      <Icon icon="lucide:sparkles" />
      <span>Build Team with AI</span>
    </button>
  )
}

export default BuildTeamButton
