# Native search workflow accepted

The search panel now stays within the visible display. The original actual UI
run showed its footer/results actions clipped; `NSHostingView.sizingOptions=[]`
lets the existing screen-bounded panel controller own its size.

**NUI01 passed once**, at `66cb4806061fe0b4e5407b740185fd0ff2f87087`, in
[run43528431516](https://github.com/alvarovillalbaa/findlet/actions/runs/43528431516)
under the [native UI scope](../../../proposals/native-search-ui.md). Actual
macOS15.8.2 ARM64/Apple Virtual Machine1, Xcode16.4, Node26.13.0/QMD2.8.3 and
real Darwin SQLite/vector bindings; no model or fake service. The normal app
had empty production-style entitlements and a verified ad-hoc signature.

The native workflow covered three actual picker selections, explicit rebuild,
three real keyword queries with the expected two matching rows, keyboard
selection and selected-original Finder reveal, Escape/global shortcut, no-match
and explicit unprepared-semantic states, native status-menu Quit, normal process
exit, retained two-document relaunch/search and confirmed Forget. Two native
scroll actions reached Forget inside the Form; the actual on-screen sheet's
button confirmed deletion, excluding its Touch Bar duplicate. One native case,
nine phases; zero failures/skips/expected failures. The prior core/K01/K02/
S01/S02/package cases did not execute.

All four empty-query panels measured690×510 at(167,111), within the1024×768
display and containing the actual AX search field. The five named empty-query
panel/menu images were inspected and retained byte-exact. Host checks verified
unchanged authored originals/runtime, retained settings, no current index
pointer and empty generations after Forget.

Images: [setup](native-ui-01-empty-setup.png), [ready](native-ui-02-ready-empty.png),
[reopened](native-ui-03-reopened-empty.png), [forgotten](native-ui-04-forgotten-empty.png),
[native menu](native-ui-05-status-menu-empty.png).

Five full guards matched136files/14,001,875bytes, vector digest
`af1e02900eda664e323bdbbdf576bac5c17dbfce78fcf7c2bff2837cd6def723`.
All30commands/60complete retained outer streams verified. Runtime query/body/
path redaction is explicit, with original hashes/sizes; these captures are not
lossless unredacted activity. Production QMD's discarded inner stderr is not
exported. The marked absent-before-launch profile, attributed processes/groups
and scratch were absent, with a passing post-removal source guard and no
controller cleanup signals. Final scratch inventory:870,588,416allocated bytes/
16,849entries. This is owned boundary evidence, not whole-host disposal proof.

Original artifact14085733868:1,152,740bytes, SHA256
`9cf682c7d75c76fde9ec14804307652d4afd0e1be2ddd16c85fb9035d26b5bd4`.
The unchanged ZIP/4,396,570-byte receipt remain in the owned local bundle;
receipt SHA256 `e73286db1136a6acc8a36d2bfa22cefcea41a92379b441356bdb369b4be44d09`.
[Curated JSON](native-search-ui.json) keeps finite observations/source/commands,
omitting only the large runtime file vector with count/digest and original
receipt binding. Private xcresult/automatic failure data was removed. Upload
proof-copy removal passed. Workflow417857183 is disabled; all ten checked task
QA refs are absent.

Nine failed originals remain: [1](native-ui-attempt-1.md),
[2](native-ui-attempt-2.md), [3](native-ui-attempt-3.md),
[4](native-ui-attempt-4.md), [5](native-ui-attempt-5.md),
[6](native-ui-attempt-6.md), [7](native-ui-attempt-7.md),
[8](native-ui-attempt-8.md), [9](native-ui-attempt-9.md).
Original3's final scratch removal/post-removal guard remain unverified. Later
success does not erase it. Earlier menu-opening inferences were qualified in
the subsequent originals; the accepted image/action now directly verify it.

This closes one authored-folder Debug UI journey. General retrieval quality,
private-folder/file-provider permissions, shortcut conflicts, strict offline,
Intel engine, Swift6 language readiness, physical/fresh downloaded Release
launch, Developer ID/notarization and Gatekeeper remain separate. The public
0.1.0 archive is unchanged; the separate0.1.1 universal packaging scope follows
this qualified source. Local Storage Guard failed; no local heavy execution.
