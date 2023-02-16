import copy
from database import crud
import pydantic_models
import config
import fastapi
from fastapi import FastAPI, Query, Body, Path

api = fastapi.FastAPI()


@api.put('/user/{user_id}')
def update_user(user_id: int, user: pydantic_models.UserToUpdate = fastapi.Body()):
    return crud.update_user(user).to_dict()


@api.delete('/user/{user_id}')
@crud.db_session
def delete_user(user_id: int = fastapi.Path()):
    crud.get_user_by_id(user_id).delete()
    return True


@api.post('/user/create')
def create_user(user: pydantic_models.UserToCreate):
    return crud.create_user(tg_id=user.tg_ID, nick=user.nick if user.nick else None).to_dict()


@api.get('/get_info_about_user/{user_id:int}')
@crud.db_session
def get_info_about_user(user_id):
    return crud.get_user_info(crud.User[user_id])


@api.get('/get_user_balance_by_id/{user_id:int}')
@crud.db_session
def get_user_balance_by_id(user_id):
    crud.update_wallet_balance(crud.User[user_id].wallet)
    return crud.User[user_id].wallet.balance


@api.get('/get_total_balance')
@crud.db_session
def get_total_balance():
    balance = 0
    crud.update_all_wallets()
    for user in crud.User.select()[:]:
        balance += user.wallet.balance
    return balance


@api.get('/get_users')
@crud.db_session
def get_users():
    users = []
    for user in crud.User.select()[:]:
        users.append(user.to_dict())
    return users


@api.get('/get_user_by_tg_id/{tg_id:int}')
@crud.db_session
def get_user_by_tg_id(tg_id):
    return crud.get_user_info(crud.User.get(tg_ID=tg_id))


@api.get('/get_user_wallet/{user_id:int}')
@crud.db_session
def get_user_wallet(user_id):
    return crud.get_wallet_info(crud.User[user_id].wallet)


# @api.post('/create_transaction')
# @crud.db_session
# def create_transaction(tg_ID: pydantic_models.TransactionCreate, receiver_address, amount_btc_without_fee, fee=None):
#     user = crud.User.get(tg_ID=tg_ID)
#     print(user, amount_btc_without_fee, receiver_address)
#     transaction = crud.create_transaction(user, amount_btc_without_fee, receiver_address, fee)
#     return transaction


@api.post('/create_transaction')
@crud.db_session
def create_transaction(transaction: pydantic_models.TransactionCreate):
    user = crud.User.get(tg_ID=transaction.tg_ID)
    transaction = crud.create_transaction(user, transaction.amount_btc_without_fee, transaction.receiver_address)
    return transaction.to_dict()


@api.get('/get_user_transactions/{user_id:int}')
@crud.db_session
def get_user_transactions(user_id):
    transactions = crud.get_user_transactions(user_id)
    return transactions
