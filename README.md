# Gwatch
Gwatch: the pipeline program for quick evaluation of sample quality in CryoEM 

## はじめに

このソフトは、単粒子像解析を行っているクライオ電顕ユーザ用に開発したpythonプログラムです。
機能はとてもシンプルで、
- 　任意のディレクトリを監視しコピー後すぐにMotionCor2, Gctfを行う（もしくはすでにあるスタックファイル）。
- 　任意の枚数に達したら、Gautomatch, Particle extraction (by Relion2), 2D-classification (by Relion2)を行う。

ここまでを一気に行うOn-the-fly Pipeline プログラムです。

そもそも開発した理由が、出来る限り早く三次元再構成がうまく行きそうかどうか、高分解能到達可能かどうかを判断するためです。

「え？おれunblur 使ってるんだけど」「ctffind4の方が良くない？」
という声があるかもしれませんが、このプログラムはあくまでもMotionCor2を速攻やって、ついでに２次元平均までを最速でやって状況判断する！がコンセプトです。
本格的な解析については、各々好きなプログラムを使用して、自分のGPGPUなどを使ってゆっくりやってください。

また、ユーザが二次元平均像から三次元再構成がうまく行きそうかどうか判断できるという前提にも立っています。
項目「判断に必要な枚数」で何枚ぐらいあればいいかをコメントしていますが、詳細については論文を書いている途中なので、もう少しお待ち下さい。

## 準備する物

K2やダイレクトディテクターなどを制御しているクライオ電顕用PCに光ファイバーやギガビットイーサネットを介して接続しているGPGPUを準備してください。
linux (ubuntuかcentOS)が載せてあれば動作可能で、GPUは二台以上積んであることが望ましいです。
また、K2の場合は４つの光ファイバーのポートの内、一つが余っています。それを有効活用することをオススメします。


## GPGPUに接続するHDDについて

私たちの場合、HDDを直接GPGPUに接続し（裸◯のお立ち台などのHDDスタンドで）、sambaサーバを介して、クライオ電顕用PCとGPGPU用PCの両方からアクセス出来るように設定しています。 また、撮影した電顕写真は直接このHDDにコピーされるように設定しています。

## インストールに必要なもの
以下の単粒子像解析用プログラム（必ずGPUで動作することを確認ください）
```
MotionCor2, Gctf, Gautomatch, eman2, IMOD, Relion2
```

- 必ずかれらの使用規約およびライセンスに則り使用してください
- MotionCor2,Gautomatch,Gctfについては、シェルから”MotionCor2”,”Gautomatch”,”Gctf”で呼び出せるようにパスもしくはエイリアスを通してください。

## 必要なpythonライブラリ (動作確認はUbuntu, CentOSでのみ):
```
python3, watchdog, pyqt5, numpy
```

Ubuntuでのインストールについて(pip経由、16.04は確認済み)
1. Python3のインストール
2. default (python3.5)
Pipのインストール
```
$ sudo apt-get install python3-dev python3-pip
```

Pipのアップグレード
```
$ sudo python3 -m pip install —upgrade pip
```

numpyのインストール
```
$ sudo python3 -m pip install numpy
```

watchdogのインストール
```
 $ sudo python3 -m pip install watchdog
```

Pyqt5のインストール
```
$ sudo  python3 -m pip install pyqt5
```


centOSでのインストールについて(pip経由、7は確認済み)
1. python3.6のインストール
```
$ sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm
$ sudo yum search python36
$ sudo yum install python36u python36u-libs python36u-devel python36u-pip
```

Pyqt5のインストール
```
$python3.6 -m pip install pyqt5
```

watchdogのインストール
```
$python3.6 -m pip install watchdog
```

Numpyのインストール
```
$python3.6 -m pip install numpy
```

## インストール方法
1. Gwatch.pyをダウンロード
2. 解凍したフォルダにパスを通す。

## Gwatchの使い方と機能について

コンソールを立ち上げて、Gwatch.pyと打ち込む。

 ### Automatic MotionCor2について
 1. “Watching Directory”について。データがコピーされるディレクトリを選ぶ
 2. “Watching File Name”について。ファイルの名前を打ち込む。このとき、ワイルドカードを使って名前を指定すること
また、スタックがmrc形式のときは"*.mrc”を使うと再帰的にmotioncor2が起動するので注意し、必ず”?”を使用し、ファイル名を限定させること（tiffもしくはmrc以外でのセーブは非推奨）
（例：file????.mrc, *.tiffなど）
 3. “Number of Frame”について。枚数の指定。シングルイメージとしてセーブされるデータに対してのみ有効。規定枚数に達したらnewstackでスタックデータを作成し、MotionCor2を起動します。（シングルイメージでのセーブは非推奨）
 4. “Do Gain-reference?” について。Gain referenceを使った補正をMotionCor2で行いたい場合はここで指定すること。YESを選んだら、”Name of Gain-Reference”からファイルを選ぶ。拡張子dm4のデータも自動で変換します。変換後は監視フォルダにgain.mrcとして保存される。
 5. “Do Measure Ice-thickness ratio?”について。YESを選ぶとエナジーフィルター有り無しの割合がmicrograph_all_gwatch.starの_rlnEnergyLossの行に記録される。その際、フィルターなしで撮影したファイルを”Name of Image without energy filter”のbrowseから一枚選ぶこと。ここではヘッダーに記録された強度から割合を求めている。
 6. “Additinal Option For MotionCor2”について。MotionCor2のオプションを入力する項目。inputとoutput、もしくはreference gain以外に必要な項目はすべてここに入力すること。-pixsizeも同様であるが、下に項目があるpixel sizeとは連動している。
 7. “Which GPUs”について。ここで使用するGPUを指定する。指定しない場合は1つのみ仕様。また、MotionCorr2使用時には,1 process毎に1GPUを割当る。最大に同時で4 process 4 GPUで計算するようにしています。なぜなら、そのほうが速いから！ 
 8. “Pixel Size”,”Cs”,”Acceleration Voltage”について。ここではGctfを計算する上で必要な数値を入力すること。ここを変更すると上記のMotionCor2のオプションと連動する。

### Automatic 2D-classificationについて
 1. "Calculate 2D classification?”について。YESを選択すると、設定した枚数に達したら二次元平均像までを行う。計算に必要な各種パラメータが入力可能となるので、必ず入力すること。結果は、Relionのdisplayを利用しポップアップされ、Class2D/job000_01、Extract/job000_01に格納される。
 2. “Calculate 2D classification every batch?”について。YESを選択すると、設定した枚数に達し次第、繰り返し二次元平均像までの計算を行う。結果は、Relionのdisplayを利用しポップアップされ、Class2D/job000_01,02… Extract/job000_01,02…と格納される。
 3. “How many Micrographs use to calculate?”について。二次元平均像を計算するときの枚数。10-50枚程度が望ましい。
 4. “Particle Diameter “について。Gautomatchで粒子をピックアップするときに必要な値。直径より小さいと多く拾うが、ゴミも多く、大きいと取り逃がすこともあるが正確に拾う傾向がある。楕円状の場合は長軸の大きさに合わすとよい思われる。
 5. “Binning”について。粒子像の抽出や二次元平均像の計算の際に適用される。ピクセルサイズによるが、counting modeだと2、super resolution modeだと4程度が望ましい。
 6. “Run”と”Cancel”について。”Run”を押すとGwatchが動く。後追いで解析可能なので、すでに数十枚取った状態からでも計算可能。また、計算がコケた場合は立ち上げ直して再度”Run”を押すと続きから計算する。この際、watching directoryは再度選び直すこと。
 ”Cancel”は計算をやめる。途中MotionCor2などが走っている場合は、その計算は投げ出される状態で終了する。

micrograph_all_gwatch.starとして、relionで利用可能な形で出力される。
この形式はGctfでの計算結果とほぼ同様である。

### タブ Results について
MotionCor2およびGctfの結果はmicrograph_all_gwatch.starから読み込み。
`“Defocus_U  Defocus_V  Angle   FoM  RationOfIcethinkness”` の順に[Results of MotionCor2 and Gctf]に表示
2D-classification実行時のコマンドラインは

[Commands For Auomatic 2D-classificaiton]で確認できる。また、監視ディレクトリ下のgwatch_cmd01.logに記録される
その他状況は

[status]で確認できる。それぞれのプログラムのエラーは赤文字表示される。

### settingファイルのsaveとopen
MotionCor2やGctf, Relion2の設定はsave settingを選ぶと記録されます。(defaultでは~/.Gwatch_settingに実行時に直近の設定がセーブされる)
呼び出しはopen settingから行えます。

## 現在の問題点と解決策
- エラーで起動しない → ライブラリのインストールを確認。それでもダメなら、"rm -rf ~/.Gwatch_setting”で初期settingファイルの消去
- たまに落ちる　→　Gwatchの再起動で解決
- MotionCor2がうまく行かない　→ データのコピーが終了せずに実行した可能性がある。
`Gwatch_v32.py -t <#time>” で起動する。`

<#time>は秒数、10などに設定するとよい。なぜなら、Gwatchはファイルの読み込み終了をファイルの増減を監視し判断しているため。インターバルタイムはdefaultだと5 secだが、10 secなど長く設定すると安全にコピー終了まで待つことができると考えられる。

## 今後実装予定の機能
 1. それぞれのプログラムへのパスの指定(2018年4月中)
 2. ネットを介した起動と結果の表示。GUIの変更およびシステムの変更(2018年6月中)
 3. 機械学習もしくはdeep learningを使った判断(未定)

## 判断に必要な枚数
10-50枚、粒子数になおすと3,000-5,000個が最終的にピックアップ出来れば判断に必要十分な量だと思います。（論文執筆中）
二次元平均像のなかに二次構造が見えるような像があれば、おそらくうまく行きます。自信をもって取れるだけ取ってください!
最後にネバーギブアップの精神でよりよりサンプル作りを頑張ってください。

## Topics
JADASやSerialEMはtiffでsaveの際にオプションでlzwでの圧縮が可能です。これを利用すると1/4~1/5まで圧縮され、かつ最新のMotionCor2でそのまま利用できます。

## 問い合わせ
もし、質問、要望、共同研究の申し出があればこちらまで　`h1839<at>fbs.osaka-u.ac.jp`



