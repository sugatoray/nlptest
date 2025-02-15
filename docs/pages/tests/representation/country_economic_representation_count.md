
## Min Country Economic Representation Count

<div class="main-docs" markdown="1"><div class="h3-box" markdown="1">

{:.h2-select}
This test checks the data regarding the sample counts of countries by economic levels.

**alias_name:** `min_country_economic_representation_count`

<i class="fa fa-info-circle"></i>
<em>This data was curated using World Bank data. To apply this test appropriately in other contexts, please adapt the [data dictionaries](https://github.com/JohnSnowLabs/nlptest/blob/main/nlptest/transform/utils.py).</em>

#### Config
```yaml
min_country_economic_representation_count:
    min_proportion: 
        high_income: 50
        low_income: 50

```
- **min_count (int):** Minimum count to pass the test.

<!-- #### Examples -->
