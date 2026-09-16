# pydantic による入力値の検証

`--driver` は `kamidana/commands/onefile.py` の
`import_symbol(args.driver, ns="kamidana.driver", cwd=True)` でドライバを
解決します。そのため、ローカルの `.py` ファイルも指定できます。

この例では pydantic v2 が必要です。pydantic は kamidana の依存関係には
含まれていないため、別途インストールしてください。

リポジトリのルートから、正常なデータをレンダリングします。

```console
$ kamidana --driver=./examples/validation/validating_driver.py:ValidatingDriver -d examples/validation/data.ok.yaml examples/validation/template.j2
hello, foo!
listening on port 8081
```

必須の `name` がなく、`port` の型も不正なデータでは、pydantic の
`ValidationError` が表示されます。

```console
$ kamidana --driver=./examples/validation/validating_driver.py:ValidatingDriver -d examples/validation/data.ng.yaml examples/validation/template.j2
```

```text
Traceback (most recent call last):
  File ".local/bin/kamidana", line 8, in <module>
  File "kamidana/commands/onefile.py", line 64, in main
    driver.run(args.template, args.dst)
  File "kamidana/driver.py", line 72, in run
    return self.dump(self.transform(self.load(src)), dst)
  File "examples/validation/validating_driver.py", line 14, in transform
    params = Params.model_validate(self.loader.data)
  File "site-packages/pydantic/main.py", line 732, in model_validate
    return cls.__pydantic_validator__.validate_python(
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Params
name
  Field required [type=missing, input_value={'port': 'not-a-number'}, input_type=CommentedMap]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
port
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not-a-number', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/int_parsing
```

`transform` の入口で検証するため、必須パラメータがない状態でテンプレートが
レンダリングされることはありません。`model_dump()` によって、テンプレート
から pydantic のデフォルト値も参照できます。
