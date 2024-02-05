<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ja_JP" sourcelanguage="en_US">
<context>
    <name>MainWindow</name>
    <message>
        <source>1. Generate a Debug Info file。
→Tag[PDBIN]
*You need to do this for the first time, but then only required when you finds some values are weird.

2. Attach to a process.

3. Start use Expression and Memory view.
→Tab[Expression] と [Memory]</source>
        <translation>1. デバッグファイルを生成する。
→タブ[PDBIN]
※最初は必要だが、それ以降は毎回する必要がない。変数の値が変な時だけ更新すればいい。

2. プロセスをアタッチする。

3. Expression が Memory を見れる。
→タブ[Expression] と [Memory]</translation>
    </message>
    <message>
        <source>1. From menu [PDB], click [Generate PDB...].

2. Choose a build folder for Visual Studio. (ie. Win32/).

3. Select a .pdb file in the left panel, then press [Generate].

4. Select a .pdbin file in the left panel, then press [Load].</source>
        <translation>1. メニュー[PDB]から、[Generate PDB...]を押す。

2. VSのビルドフォルダを選択する。例えば Win32/。

3. 左側の.pdbファイルを選択して、[Generate]を押す。

4. 右側の.pdbinファイルを選択して、[Load]を押す。</translation>
    </message>
    <message>
        <source>1. Input an address, then press Enter to vew memory.

2. Default size is 1024 bytes.

3. More actions in the top-right [☰] menu.</source>
        <translation>1. アドレスを入力して、エンターキーを押すと、メモリが表示される。

2. サイズのデフォルト値は1024 bytes。

3. 右上の[☰]メニューから、他の機能がある。</translation>
    </message>
    <message>
        <source>1. Input an expression, then press Enter to view the structure.
* Current limitations for expression:

- Global variable references, ie.
  gModule
  gModule.attribute
  gModule.buffer-&gt;attr

- Cast a pointer from an address, ie.
  (ModelStruct *)0x1234

2. Value modification will be written to the process in real-time

3. If you want to refresh all values, please click [Refresh] from top-right [☰] menu.

4. PVOID type is editable.

5. Count value for pointer is also editable.</source>
        <translation>1. Expressionを入力して、エンターキー押すと、構造が見れる。
※今入力可能なExpressionは以下に説明する。

- グローバル変数からの参照。例えば：
  gModule
  gModule.attribute
  gModule.buffer-&gt;attr

- アドレスをポインタ型にカスト
  (ModelStruct *)0x1234

2. 変数の値を変えると、リアルタイムに反映される。

3. 変数の値を更新したい時、右上の[☰]メニューから。

4. PVOID 型は変更可能。

5. ポインタ型のCount値は変更可能。</translation>
    </message>
    <message>
        <source>Tool</source>
        <translation>ツール</translation>
    </message>
    <message>
        <source>How to use?</source>
        <translation>使い方</translation>
    </message>
</context>
</TS>
