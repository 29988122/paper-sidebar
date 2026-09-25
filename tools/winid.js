// osascript -l JavaScript tools/winid.js <pid>   on-screen normal windows of <pid> as JSON, largest first
// osascript -l JavaScript tools/winid.js front   PID of the frontmost application
ObjC.import("CoreGraphics");
ObjC.import("AppKit");

function run(argv) {
  if (argv[0] === "front") {
    return String($.NSWorkspace.sharedWorkspace.frontmostApplication.processIdentifier);
  }
  const pid = Number(argv[0]);
  const ON_SCREEN_ONLY = 1, EXCLUDE_DESKTOP = 16, NULL_WINDOW = 0;
  const list = ObjC.castRefToObject($.CGWindowListCopyWindowInfo(ON_SCREEN_ONLY | EXCLUDE_DESKTOP, NULL_WINDOW));
  const wins = [];
  for (let i = 0; i < list.count; i++) {
    const w = ObjC.deepUnwrap(list.objectAtIndex(i));
    const b = w.kCGWindowBounds;
    if (w.kCGWindowOwnerPID === pid && w.kCGWindowLayer === 0 && b.Width >= 600) {
      wins.push({ id: w.kCGWindowNumber, x: b.X, y: b.Y, width: b.Width, height: b.Height });
    }
  }
  wins.sort((a, b) => b.width * b.height - a.width * a.height);
  return JSON.stringify(wins);
}
