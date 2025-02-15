
## Min Ethnicity Representation Proportion

<div class="main-docs" markdown="1"><div class="h3-box" markdown="1">

{:.h2-select}
This test checks the data regarding the sample proportions of ethnicities.

**alias_name:** `min_ethnicity_name_representation_proportion`

<i class="fa fa-info-circle"></i>
<em>This data was curated using 2021 US census survey data. To apply this test appropriately in other contexts, please adapt the [data dictionaries](https://github.com/JohnSnowLabs/nlptest/blob/main/nlptest/transform/utils.py).</em>

#### Config
```yaml
min_ethnicity_name_representation_proportion:
    min_proportion: 
        white: 0.20
        black: 0.36                
```

- **min_proportion (float):** Minimum proportion to pass the test.

<!-- #### Examples -->
