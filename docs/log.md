# log


## claude code install


claude code使ってみる


```

# install nodejs
<!-- https://nodejs.org/en/download -->
# Download and install fnm:
curl -o- https://fnm.vercel.app/install | bash

# install fnm (node version manager)
curl -fsSL https://fnm.vercel.app/install | bash
# Download and install Node.js:
fnm install 22

# Verify the Node.js version:
node -v # Should print "v22.16.0".

# Verify npm version:
npm -v # Should print "10.9.2".


# install claude code
npm install -g @anthropic-ai/claude-code

```

## claude codeの設定色々

https://www.anthropic.com/engineering/claude-code-best-practices

### GitHub CLIのインストールと認証

ghのインストール・認証
https://qiita.com/cointoss1973/items/54ce4967ed2d09c3bbc1

```

sudo apt install gh

gh auth login
gh auth setup-git

```

ghコマンドの補完
.bashrcにeval "$(gh completion -s bash)"を追加
>>を使って、

```bash
# Add GitHub CLI completion to .bashrc
echo 'eval "$(gh completion -s bash)"' >> ~/.bashrc
source ~/.bashrc
```

## claude code 実際に使ってみる

まずは開発計画を立てさせる。
色々なプラクティス
https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices


### test

```bash
# youtubeから拾ってきた音声データでテスト
python test_real_audio.py data/input/input_wav.wav ./output


```

### pyannote-audioの認証トークン設定

export HF_TOKEN=your_token_hereする

```bash
export HF_TOKEN=hf_xxx # ここに自分のトークンを入れる
```


### claude codeの使用料量などの確認

https://zenn.dev/ryoppippi/articles/6c9a8fe6629cd6

```bash
# Check usage
npx ccusage@latest

# 日別レポート
npx ccusage daily

# セッション別レポート
npx ccusage session

