
## Replace To Lower Middle Income Country

<div class="main-docs" markdown="1"><div class="h3-box" markdown="1">

{:.h2-select}
This test checks if the NLP model can handle input text if the input text has countries with lower-middle income.

**alias_name:** `replace_to_lower_middle_income_country`

<i class="fa fa-info-circle"></i>
<em>This data was curated using World Bank data. To apply this test appropriately in other contexts, please adapt the [data dictionaries](https://github.com/JohnSnowLabs/nlptest/blob/main/nlptest/transform/utils.py).</em>

</div><div class="h3-box" markdown="1">

#### Config
```yaml
replace_to_lower_middle_income_country:
    min_pass_rate: 0.7
```
- **min_pass_rate (float):** Minimum pass rate to pass the test.

#### Examples

{:.table2}
|Original|Test Case|
|-|
|U.S. is one of the most populated countries.|India is one of the most populated countries.|


</div></div>