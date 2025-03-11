

int err;


err = rhltable_init(&mrt->mfc_hash, &ipmr_rht_params);


if (err) {


kfree(mrt);


return ERR_PTR(err);


}
