
## Replace To Female Pronouns

<div class="main-docs" markdown="1"><div class="h3-box" markdown="1">

{:.h2-select}
This test checks if the NLP model can handle input text if the input text has female pronouns.

**alias_name:** `replace_to_female_pronouns`

<i class="fa fa-info-circle"></i>
<em>This data was curated using publicly available records. To apply this test appropriately in other contexts, please adapt the [data dictionaries](https://github.com/JohnSnowLabs/nlptest/blob/main/nlptest/transform/utils.py).</em>

</div><div class="h3-box" markdown="1">

#### Config
```yaml
replace_to_female_pronouns:
    min_pass_rate: 0.7
```
- **min_pass_rate (float):** Minimum pass rate to pass the test.

#### Examples

{:.table2}
|Original|Test Case|
|-|
|He is brilliant.|She is brilliant.|
|He forgot his keys at the office.|She forgot her keys at the office.|


</div></div>