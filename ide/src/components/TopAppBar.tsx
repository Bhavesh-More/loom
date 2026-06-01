import MaterialIcon from './MaterialIcon'

function TopAppBar() {
  return (
    <header className="top-app-bar">
      <nav className="top-app-bar__links" aria-label="Workspace sections">
        <a className="label-text" href="#">
          Models
        </a>
      </nav>

      <div className="top-app-bar__actions">
        <button className="icon-button" type="button" aria-label="Open grid view">
          <MaterialIcon name="grid_view" />
        </button>
        <button className="icon-button" type="button" aria-label="Toggle right sidebar">
          <MaterialIcon name="view_sidebar" />
        </button>
      </div>
    </header>
  )
}

export default TopAppBar
